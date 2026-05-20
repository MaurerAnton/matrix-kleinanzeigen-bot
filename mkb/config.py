import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

MATRIX_HOMESERVER = os.environ.get("MATRIX_HOMESERVER", "https://matrix.org")
MATRIX_USER = os.environ.get("MATRIX_USER", "")
MATRIX_PASSWORD = os.environ.get("MATRIX_PASSWORD", "")
MATRIX_ACCESS_TOKEN = os.environ.get("MATRIX_ACCESS_TOKEN", "")

_default_db = str(Path(__file__).resolve().parent.parent / "data" / "kleinanzeigen.db")
DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite+aiosqlite:///{_default_db}")
CHECK_INTERVAL = int(os.environ.get("CHECK_INTERVAL", "600"))  # seconds
