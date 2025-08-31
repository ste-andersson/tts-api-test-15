# Text validation module

# Text-validering inställningar
MAX_TEXT_CHARS = 1000  # Max antal tecken för text-input

async def receive_and_validate_text(ws):
    # 1) Ta emot klientens första meddelande
    raw = await ws.receive_text()
    try:
        data = json.loads(raw)
    except Exception:
        await _send_json(ws, {"type": "error", "message": "Invalid JSON"})
        await ws.close(code=1003)
        return

    text: Optional[str] = (data.get("text") or "").strip()

    if not text:
        await _send_json(ws, {"type": "error", "message": "Tom text"})
        await ws.close(code=1003)
        return

    if len(text) > MAX_TEXT_CHARS:
        await _send_json(ws, {"type": "error", "message": f"Max {MAX_TEXT_CHARS} tecken"})
        await ws.close(code=1009)
        return

    return {"text": text}



