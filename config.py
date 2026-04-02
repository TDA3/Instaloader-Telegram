import os
from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

IG_USERNAME = os.getenv("IG_USERNAME", "")
IG_SESSION_FILE = os.getenv("IG_SESSION_FILE", "cookies/session")
DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR", "downloads")

# Admin / access control
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
_allowed_raw = os.getenv("ALLOWED_USERS", "").strip()
ALLOWED_USERS: list[int] = (
    [int(uid) for uid in _allowed_raw.split(",") if uid.strip()]
    if _allowed_raw
    else []
)
LOG_CHANNEL = int(os.getenv("LOG_CHANNEL", "0"))

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Rate limiting
COOLDOWN_SECONDS = int(os.getenv("COOLDOWN_SECONDS", "5"))
