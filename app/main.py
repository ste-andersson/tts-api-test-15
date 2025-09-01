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
from .endpoints.health import healthz, echo
from .endpoints.tts_ws import ws_tts
from .endpoints.test import router as test_router
from .endpoints.audio_viewer import router as audio_router

logger = logging.getLogger("stefan-api-test-3")
logging.basicConfig(level=logging.DEBUG)

app = FastAPI(title="stefan-api-test-3", version="0.1.3")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[],
    allow_origin_regex=settings.ALLOWED_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrera endpoints
app.get("/healthz")(healthz)
app.post("/echo")(echo)
app.websocket("/ws/tts")(ws_tts)
app.include_router(test_router, prefix="/api")
app.include_router(audio_router, prefix="/api")












