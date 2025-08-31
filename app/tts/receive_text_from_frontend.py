# Text validation module

async def receive_and_validate_text(ws, settings):
    # 1) Ta emot klientens första meddelande
    raw = await ws.receive_text()
    try:
        data = json.loads(raw)
    except Exception:
        await _send_json(ws, {"type": "error", "message": "Invalid JSON"})
        await ws.close(code=1003)
        return

    text: Optional[str] = (data.get("text") or "").strip()
    voice_id: str = data.get("voice_id") or settings.DEFAULT_VOICE_ID
    model_id: str = data.get("model_id") or settings.DEFAULT_MODEL_ID

    if not text:
        await _send_json(ws, {"type": "error", "message": "Tom text"})
        await ws.close(code=1003)
        return

    if len(text) > settings.MAX_TEXT_CHARS:
        await _send_json(ws, {"type": "error", "message": f"Max {settings.MAX_TEXT_CHARS} tecken"})
        await ws.close(code=1009)
        return



