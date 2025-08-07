# app/config.py
from pathlib import Path
import os
from datetime import datetime, timezone
from dotenv import load_dotenv

now = datetime.now(timezone.utc).isoformat()[:19]

load_dotenv()

ROOT_PATH = Path(os.getenv("ROOT_PATH", "/music")).resolve()
CONFIG_PATH = Path(os.getenv("CONFIG_PATH", "./config")).resolve()

ARTISTS_FILE = CONFIG_PATH / "artists.json"
LAST_RUN_FILE = CONFIG_PATH / "last_run.json"

# Intervalo en días para la ejecución del scheduler (default 5)
SCHEDULE_INTERVAL_DAYS = int(os.getenv("SCHEDULE_INTERVAL_DAYS", "5"))