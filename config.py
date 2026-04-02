import os
from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

IG_USERNAME = os.getenv("IG_USERNAME", "")
IG_SESSION_FILE = os.getenv("IG_SESSION_FILE", "cookies/session")
DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR", "downloads")
