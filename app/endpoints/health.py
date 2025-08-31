import logging
from fastapi import HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger("stefan-api-test-3")

class EchoIn(BaseModel):
    text: str = Field(..., max_length=1000)

async def healthz():
    """Health check endpoint."""
    return {"ok": True, "service": "stefan-api-test-3"}

async def echo(payload: EchoIn):
    """Echo endpoint för att testa text-input."""
    length = len(payload.text or "")
    logger.info("Echo text received: %s chars", length)
    
    if length > 1000:  # Hårdkodad som i receive_text_from_frontend
        raise HTTPException(
            status_code=400,
            detail=f"Texten är för lång (>1000).",
        )
    
    return {"received_chars": length}
