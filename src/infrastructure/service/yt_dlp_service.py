# app/service/console.reader.service.py
from typing import Tuple, Optional, Callable, List, Dict
import json
import random
import time
from typing import Dict
from src.application.providers.logger_provider import LoggerProvider
from src.infrastructure.config.config import COOKIES_FILE, METADATA_SONGS_CACHE
from src.infrastructure.system.json_loader import metadata_cache_load
from src.infrastructure.system.subprocess_runner import run_subprocess_with_detectors

logger= LoggerProvider()

def detect_ip_ban(line: str, returncode: int) -> bool:
    patterns = [
        "Sign in to confirm you’re not a bot",
        "Sign in to confirm you're not a bot",
        "Use --cookies-from-browser or --cookies for the authentication"
    ]
    if any(p in line for p in patterns):
        logger.error("🚫 YouTube ha bloqueado temporalmente la IP (captcha / bot check).")
        return True, True
    return False, False

def detect_video_unavailable(line: str, returncode: int) -> Tuple[bool, bool]:
    """
    Devuelve (detected, critical):
      - detected: True si coincidió con el patrón
      - critical: True si debe detener todo el proceso
    """
    patterns = [
        "Video unavailable",
        "This video is not available"
    ]
    if any(p in line for p in patterns):
        logger.error(f"🚫 Video no disponible")
        return True, False  # no es crítico
    return False, False

def detect_no_videos(line: str, returncode: int) -> bool:
    """
    Detecta cuando yt-dlp finaliza sin descargar nada porque no hay vídeos válidos.
    Esto ocurre típicamente con el código de salida 101:
      - Playlist vacía.
      - Todos los vídeos ya descargados o no disponibles.
      - Filtros (ej. --dateafter) que descartan todos los vídeos.
    
    Si se detecta, se registra una advertencia en el log y devuelve True
    para que el proceso no se considere un error crítico.
    """
    if returncode == 101 or "No videos to download" in line or "no videos" in line.lower():
        logger.warning("⚠️ El video de la playlist que se esta analizando, no es nuevo.")
        return True, False
    return False, False


ERROR_DETECTORS = [
    detect_ip_ban,
    detect_video_unavailable,
    detect_no_videos,
]

def run_yt_dlp(command: list[str]) -> tuple[bool, bool]:
    """
    Ejecuta yt-dlp usando run_subprocess_with_detectors.
    Devuelve (success, critical):
      - success: True si no se detectó ningún error crítico.
      - critical: True si se detectó un error crítico.
    """
    output, (success, critical), detected_error, returncode = run_subprocess_with_detectors(
        command, ERROR_DETECTORS
    )

    # Opcional: detectar descarga completada desde la salida
    for line in output.splitlines():
        if line.startswith("[ExtractAudio] Destination:") or "has already been downloaded" in line:
            title = line.split("Destination:")[-1].strip() if "Destination:" in line else line
            logger.info(f"🎵 Descargado: {title}")

    return success, critical


# Cache temporal en memoria para batch
_batch_cache: Dict[str, Dict] = {}
_disk_cache: Dict[str, Dict] = metadata_cache_load()  # Carga inicial desde json_loader

def save_batch_cache():
    """Guarda en disco las entradas acumuladas en _batch_cache"""
    global _batch_cache, _disk_cache
    if not _batch_cache:
        return

    # Actualizar cache en disco con batch
    _disk_cache.update(_batch_cache)

    with METADATA_SONGS_CACHE.open("w", encoding="utf-8") as f:
        json.dump(_disk_cache, f, ensure_ascii=False, indent=2)

    _batch_cache.clear()


#comprobamos que una url este en la cache
def is_url_in_cache(url: str) -> bool:
    return url in _disk_cache

def fetch_raw_metadata(url: str) -> Dict | None:
    global _batch_cache, _disk_cache


    if url in _disk_cache:
        return _disk_cache[url]

    time.sleep(random.uniform(5, 10))

    cmd = ["yt-dlp", "-j", "--skip-download", url]
    if COOKIES_FILE.exists():
        cmd += ["--cookies", str(COOKIES_FILE)]

    output, (success, critical), detected_error,returncode = run_subprocess_with_detectors(cmd, ERROR_DETECTORS)

    if not success:
        if detected_error and "Video unavailable" in detected_error:
            _batch_cache[url] = {}
            _disk_cache[url] = {}
        if critical:
            return None
    
    try:
        info = json.loads(output)
    except json.JSONDecodeError:
        raise RuntimeError(f"Salida inválida de yt-dlp para {url}")

    artist_str = "; ".join(info.get("artists", [])) if isinstance(info.get("artists"), list) else str(info.get("artist", ""))

    filtered_info = {
        "id": info.get("id"),
        "title": info.get("title"),
        "album": info.get("album"),
        "date": info.get("release_date"),
        "artist": artist_str
    }

    _batch_cache[url] = filtered_info
    _disk_cache[url] = filtered_info
    return filtered_info

def flush_batch_cache():
    """Forzar guardado de cualquier batch pendiente"""
    save_batch_cache()