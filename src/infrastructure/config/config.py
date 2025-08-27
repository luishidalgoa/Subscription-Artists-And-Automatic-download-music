# app/infrastructure/config/config.py
import os
from pathlib import Path
from datetime import datetime, timezone
from dotenv import load_dotenv

# Ruta a la carpeta /config en el root del proyecto
CONFIG_DIR = Path(__file__).resolve().parent.parent.parent.parent / "config"

# Cargar variables de entorno desde /config/.env
load_dotenv(dotenv_path=CONFIG_DIR / ".env")

# Timestamp actual (útil para logs o last_run.json)
now = datetime.now(timezone.utc).isoformat()[:19]

def update_now():
    """Refresca la variable global `now`."""
    global now
    now = datetime.now(timezone.utc).isoformat()[:19]

# Paths principales
ROOT_PATH = Path(os.getenv("ROOT_PATH", "/music")).resolve()
CONFIG_PATH = Path(os.getenv("CONFIG_PATH", CONFIG_DIR)).resolve()

# Archivos de configuración persistente
ARTISTS_FILE = CONFIG_PATH / "artists.json"
LAST_RUN_FILE = CONFIG_PATH / "last_run.json"
COOKIES_FILE = Path(os.getenv("COOKIES_FILE", CONFIG_PATH / "_cookies.txt")).resolve()

# Base de datos
DB_PATH = Path(os.getenv("DB_PATH", "data/db.sqlite")).resolve()
