from pydantic import BaseModel
import os

class Settings(BaseModel):
    # Regex som matchar Lovable-subdomäner och localhost under dev
    ALLOWED_ORIGIN_REGEX: str = os.getenv(
        "ALLOWED_ORIGIN_REGEX",
        r"^https?://(localhost(:\d+)?|.*\.lovable\.app)$",
    )

settings = Settings()
