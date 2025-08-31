import asyncio
import base64
import json
import logging
import time
from websockets.client import connect as ws_connect
import orjson

logger = logging.getLogger("stefan-api-test-3")


async def process_text_to_audio(ws, text, voice_id, model_id, settings, started_at):
    """Hanterar ElevenLabs API-kommunikation och audio-streaming."""
    
    # 2) Anslut till ElevenLabs
    # Behåll mp3_44100_64 för kompatibilitet med fallback i frontend
    query = f"?model_id={model_id}&output_format=pcm_16000"
    eleven_ws_url = f"wss://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream-input{query}"
    headers = [("xi-api-key", settings.ELEVENLABS_API_KEY)]

    audio_bytes_total = 0
    last_chunk_ts = None
    inactivity_timeout_sec = 12  # intern timeout efter att vi sagt "streaming"

    async with ws_connect(eleven_ws_url, extra_headers=headers, open_timeout=30) as eleven:
        # 3) Initiera session
        init_msg = {
            "text": " ",  # kickstart
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.8,
                "use_speaker_boost": False,
                "speed": 1.0,
            },
            "generation_config": {
                # Lägre trösklar → snabbare start på kort text
                "chunk_length_schedule": [50, 90, 140]
            },
            "xi_api_key": settings.ELEVENLABS_API_KEY,
        }
        await eleven.send(orjson.dumps(init_msg).decode())
        logger.debug("Sent init message to ElevenLabs")

        # 4) Skicka text och trigga generering direkt
        await eleven.send(orjson.dumps({"text": text, "try_trigger_generation": True}).decode())
        logger.debug("Sent user text (%d chars) with try_trigger_generation=True", len(text))

        # 5) Avsluta inmatning (förhindra deras 20s-timeout)
        await eleven.send(orjson.dumps({"text": "", "flush": True}).decode())
        logger.debug("Sent flush message to ElevenLabs")

        await _send_json(ws, {"type": "status", "stage": "streaming"})

        # 6) Läs streamen och vidarebefordra
        while True:
            try:
                server_msg = await asyncio.wait_for(eleven.recv(), timeout=inactivity_timeout_sec)
            except asyncio.TimeoutError:
                # Vi har inte fått något på N sekunder → ge upp snyggt
                logger.warning("No data from ElevenLabs for %ss, aborting stream", inactivity_timeout_sec)
                await _send_json(ws, {
                    "type": "error",
                    "message": f"Ingen data från TTS på {inactivity_timeout_sec}s. Avbryter.",
                })
                break

            # ElevenLabs skickar (vanligen) JSON‐text
            try:
                payload = json.loads(server_msg)
            except Exception:
                # Om binärt (ovanligt), skicka vidare
                if isinstance(server_msg, (bytes, bytearray)):
                    await ws.send_bytes(server_msg)
                    audio_bytes_total += len(server_msg)
                    last_chunk_ts = time.time()
                    logger.debug("Forwarded binary frame: %d bytes", len(server_msg))
                else:
                    logger.debug("Non-JSON non-bytes frame received (ignored)")
                continue

            # Debug: skicka upp event/meta till frontend (utan base64-datan)
            meta = {k: v for k, v in payload.items() if k not in ("audio", "normalizedAlignment", "alignment")}
            await _send_json(ws, {"type": "debug", "provider": "elevenlabs", "payload": meta})
            logger.debug("ElevenLabs frame keys=%s", list(payload.keys()))

            # Fel från ElevenLabs?
            if payload.get("event") == "error" or "error" in payload:
                err_msg = payload.get("message") or payload.get("error") or "Okänt fel från TTS-leverantören"
                logger.error("ElevenLabs error: %s", err_msg)
                await _send_json(ws, {"type": "error", "message": err_msg})
                break

            # Audio‐chunk (base64) – kan vara null/tom → hoppa över
            audio_b64 = payload.get("audio")
            if isinstance(audio_b64, str) and audio_b64:
                try:
                    b = base64.b64decode(audio_b64)
                    if b:
                        await ws.send_bytes(b)
                        audio_bytes_total += len(b)
                        last_chunk_ts = time.time()
                        logger.debug("Forwarded audio chunk: %d bytes (total=%d)", len(b), audio_bytes_total)
                except Exception as e:
                    logger.warning("Kunde inte dekoda audio-chunk: %s", e)

            # Slut?
            if payload.get("isFinal") is True or payload.get("event") == "finalOutput":
                logger.debug("Final frame from ElevenLabs received")
                break

        await _send_json(ws, {
            "type": "status",
            "stage": "done",
            "audio_bytes_total": audio_bytes_total,
            "elapsed_sec": round(time.time() - started_at, 3),
        })
        logger.info("Stream done: audio_bytes_total=%d elapsed=%.3fs", audio_bytes_total, time.time() - started_at)
        
        return audio_bytes_total


async def _send_json(ws, obj: dict):
    """Skicka JSON (utf-8) till frontend."""
    try:
        await ws.send_text(json.dumps(obj))
    except Exception as e:
        logger.error("Failed to send JSON: %s", e)
