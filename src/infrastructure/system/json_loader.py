# src/infrastructure/system/json_loader.py
import json
from src.application.providers.logger_provider import LoggerProvider
from src.infrastructure.config.config import ARTISTS_FILE, LAST_RUN_FILE, METADATA_SONGS_CACHE, ROOT_PATH

logger = LoggerProvider()
def artists_load():
    if ARTISTS_FILE.exists():
        try:
            with ARTISTS_FILE.open() as f:
                artists = json.load(f)
                return artists
        except Exception as e:
            logger.error(f"Error al leer artists.json: {e}")
            return
    else:
        return {}

def last_run_load():
    if LAST_RUN_FILE.exists():
        try:
            with LAST_RUN_FILE.open() as f:
                last_run = json.load(f)
                return last_run
        except Exception as e:
            logger.error(f"Error al leer last_run.json: {e}")
            return
    else:
        return {}

def metadata_cache_load() -> dict:
    """Carga la cache de metadatos desde disco"""
    if METADATA_SONGS_CACHE.exists():
        try:
            with METADATA_SONGS_CACHE.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error al leer metadata_songs_cache.json: {e}")
            return {}
    return {}