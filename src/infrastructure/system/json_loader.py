# src/infrastructure/system/json_loader.py
import json
from src.application.providers.logger_provider import LoggerProvider
from src.infrastructure.config.config import ARTISTS_FILE, LAST_RUN_FILE, METADATA_SONGS_CACHE, MUSIC_ROOT_PATH

logger = LoggerProvider()
def artists_load():
    # Devuelve SIEMPRE una lista (vacía ante error/ausencia) para que los bucles
    # `for artist in artists` no revienten con None o con un tipo inesperado.
    if ARTISTS_FILE.exists():
        try:
            with ARTISTS_FILE.open() as f:
                artists = json.load(f)
                return artists if isinstance(artists, list) else []
        except Exception as e:
            logger.error(f"Error al leer artists.json: {e}")
            return []
    else:
        return []

def last_run_load():
    # Devuelve SIEMPRE un dict (vacío ante error/ausencia) para poder hacer .get().
    if LAST_RUN_FILE.exists():
        try:
            with LAST_RUN_FILE.open() as f:
                last_run = json.load(f)
                return last_run if isinstance(last_run, dict) else {}
        except Exception as e:
            logger.error(f"Error al leer last_run.json: {e}")
            return {}
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