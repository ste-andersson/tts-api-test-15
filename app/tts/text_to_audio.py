import asyncio
import logging
import time
import os
from websockets.client import connect as ws_connect
import orjson

logger = logging.getLogger("stefan-api-test-3")

# TTS-specifika inställningar
DEFAULT_VOICE_ID = "kkwvaJeTPw4KK0sBdyvD"  # Sätt ditt voice-ID här
DEFAULT_MODEL_ID = "eleven_flash_v2_5"
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")  # Hämtas från .env


async def process_text_to_audio(ws, text, started_at):
    """Hanterar ElevenLabs API-kommunikation och returnerar rå data."""
    
    # 2) Anslut till ElevenLabs
    query = f"?model_id={DEFAULT_MODEL_ID}&output_format=pcm_16000"
    eleven_ws_url = f"wss://api.elevenlabs.io/v1/text-to-speech/{DEFAULT_VOICE_ID}/stream-input{query}"
    headers = [("xi-api-key", ELEVENLABS_API_KEY)]
    
    # Logga API-detaljer i terminalen
    logger.info("Connecting to ElevenLabs with voice_id=%s, model_id=%s", DEFAULT_VOICE_ID, DEFAULT_MODEL_ID)
    
    # Skicka API-detaljer till frontend för debugging
    import json
    try:
        await ws.send_text(json.dumps({
            "type": "debug", 
            "provider": "elevenlabs", 
            "api_details": {
                "voice_id": DEFAULT_VOICE_ID,
                "model_id": DEFAULT_MODEL_ID,
                "url": eleven_ws_url,
                "has_api_key": bool(ELEVENLABS_API_KEY)
            }
        }))
    except Exception as e:
        logger.warning("Failed to send debug info to frontend: %s", e)

    audio_bytes_total = 0
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
            "xi_api_key": ELEVENLABS_API_KEY,
        }
        await eleven.send(orjson.dumps(init_msg).decode())
        logger.debug("Sent init message to ElevenLabs")
        
        # Skicka init-meddelandet till frontend för debugging
        try:
            await ws.send_text(json.dumps({
                "type": "debug",
                "provider": "elevenlabs", 
                "init_message": {
                    "text": init_msg["text"],
                    "voice_settings": init_msg["voice_settings"],
                    "generation_config": init_msg["generation_config"],
                    "has_api_key": bool(init_msg["xi_api_key"])
                }
            }))
        except Exception as e:
            logger.warning("Failed to send init debug info to frontend: %s", e)

        # 4) Skicka text och trigga generering direkt
        await eleven.send(orjson.dumps({"text": text, "try_trigger_generation": True}).decode())
        logger.debug("Sent user text (%d chars) with try_trigger_generation=True", len(text))

        # 5) Avsluta inmatning (förhindra deras 20s-timeout)
        await eleven.send(orjson.dumps({"text": "", "flush": True}).decode())
        logger.debug("Sent flush message to ElevenLabs")

        # 6) Läs streamen och returnera rå data
        while True:
            try:
                server_msg = await asyncio.wait_for(eleven.recv(), timeout=inactivity_timeout_sec)
            except asyncio.TimeoutError:
                # Vi har inte fått något på N sekunder → ge upp snyggt
                logger.warning("No data from ElevenLabs for %ss, aborting stream", inactivity_timeout_sec)
                break

            # Returnera rå data från ElevenLabs
            yield server_msg, audio_bytes_total

            # Uppdatera audio_bytes_total för binary frames
            if isinstance(server_msg, (bytes, bytearray)):
                audio_bytes_total += len(server_msg)

            # Slut?
            if isinstance(server_msg, str):
                try:
                    payload = orjson.loads(server_msg)
                    if payload.get("isFinal") is True or payload.get("event") == "finalOutput":
                        logger.debug("Final frame from ElevenLabs received")
                        break
                except:
                    pass

        logger.info("Stream done: audio_bytes_total=%d elapsed=%.3fs", audio_bytes_total, time.time() - started_at)
