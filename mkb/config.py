import os

from dotenv import load_dotenv

load_dotenv()

MATRIX_HOMESERVER = os.environ.get("MATRIX_HOMESERVER", "https://matrix.org")
MATRIX_USER = os.environ.get("MATRIX_USER", "")
MATRIX_PASSWORD = os.environ.get("MATRIX_PASSWORD", "")
MATRIX_ACCESS_TOKEN = os.environ.get("MATRIX_ACCESS_TOKEN", "")
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite+aiosqlite:///data/kleinanzeigen.db")
CHECK_INTERVAL = int(os.environ.get("CHECK_INTERVAL", "600"))  # seconds
