import asyncio
import base64
import json
import logging
import time
from typing import Optional

import orjson
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from websockets.client import connect as ws_connect
from websockets.exceptions import ConnectionClosedOK, ConnectionClosedError
from dotenv import load_dotenv

# Ladda .env-filen
load_dotenv()

from .config import settings
from .tts.receive_text_from_frontend import receive_and_validate_text
from .tts.text_to_audio import process_text_to_audio
from .tts.send_audio_to_frontend import send_audio_to_frontend

logger = logging.getLogger("stefan-api-test-3")
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="stefan-api-test-3", version="0.1.3")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[],
    allow_origin_regex=settings.ALLOWED_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class EchoIn(BaseModel):
    text: str = Field(..., max_length=1000)


@app.get("/healthz")
async def healthz():
    return {"ok": True, "service": "stefan-api-test-3"}


@app.post("/echo")
async def echo(payload: EchoIn):
    length = len(payload.text or "")
    logger.info("Echo text received: %s chars", length)
    if length > settings.MAX_TEXT_CHARS:
        raise HTTPException(
            status_code=400,
            detail=f"Texten är för lång (>{settings.MAX_TEXT_CHARS}).",
        )
    return {"received_chars": length}


async def _send_json(ws: WebSocket, obj: dict):
    """Skicka JSON (utf-8) till frontend."""
    try:
        await ws.send_text(orjson.dumps(obj).decode())
    except Exception:
        # Faller tillbaka till standardjson om orjson av någon anledning felar
        await ws.send_text(json.dumps(obj))


@app.websocket("/ws/tts")
async def ws_tts(ws: WebSocket):
    await ws.accept()
    started_at = time.time()
    try:
        await _send_json(ws, {"type": "status", "stage": "ready"})

        # 1) Ta emot och validera text från frontend
        text_data = await receive_and_validate_text(ws)
        if text_data is None:
            return  # receive_and_validate_text hanterar fel och stänger ws
        
        text = text_data["text"]

        await _send_json(ws, {"type": "status", "stage": "connecting-elevenlabs"})
        logger.debug("Connecting to ElevenLabs")

        # 2) Hantera ElevenLabs API-kommunikation och audio-streaming
        await _send_json(ws, {"type": "status", "stage": "streaming"})
        
        audio_bytes_total = 0
        last_chunk_ts = None
        
        async for server_msg, current_audio_bytes in process_text_to_audio(ws, text, started_at):
            # Hantera audio-streaming till frontend
            audio_bytes_total, last_chunk_ts, should_break = await send_audio_to_frontend(
                ws, server_msg, current_audio_bytes, last_chunk_ts
            )
            
            if should_break:
                break
        
        await _send_json(ws, {
            "type": "status",
            "stage": "done",
            "audio_bytes_total": audio_bytes_total,
            "elapsed_sec": round(time.time() - started_at, 3),
        })


    except WebSocketDisconnect:
        logger.info("Client disconnected")
    except (ConnectionClosedOK, ConnectionClosedError) as e:
        logger.info("Upstream WS closed: %s", e)
    except Exception as e:
        logger.exception("WS error: %s", e)
        try:
            await _send_json(ws, {"type": "error", "message": str(e)})
        except Exception:
            pass
        try:
            await ws.close(code=1011)
        except Exception:
            pass
