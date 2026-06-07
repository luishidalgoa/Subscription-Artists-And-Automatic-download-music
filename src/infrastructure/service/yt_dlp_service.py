# app/service/console.reader.service.py
from typing import Tuple, Optional, Callable, List, Dict
import json
import random
import shutil
import sys
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

def detect_js_error(line: str, returncode: int) -> Tuple[bool, bool]:
    # NO es crítico: son advertencias de yt-dlp al no resolver el challenge JS de YouTube
    # (falta el solver EJS). Para AUDIO (opus/m4a) la descarga funciona igual — verificado.
    # Antes se marcaba crítico y abortaba TODO el run en la primera pista.
    if "Signature solving failed" in line or "n challenge solving failed" in line:
        logger.warning("⚠️ yt-dlp no resolvió el challenge JS (pueden faltar formatos de vídeo; el audio se baja igual).")
        return True, False
    return False, False

ERROR_DETECTORS = [
    detect_ip_ban,
    detect_video_unavailable,
    detect_no_videos,
    detect_js_error,
]

# Separador (Unit Separator, 0x1f) que usa el template --print de yt-dlp: nunca aparece
# en títulos/álbumes, así que distingue las líneas de progreso del resto de la salida.
PROGRESS_SEP = "\x1f"
# Template para --print "before_dl:...": emite "<sep><álbum><sep><título>" por canción.
# album cae a playlist_title (releases) y por defecto a "Sin álbum".
PROGRESS_PRINT = f"before_dl:{PROGRESS_SEP}%(album,playlist_title|Sin álbum)s{PROGRESS_SEP}%(title)s"


def _progress_renderer():
    """Devuelve un callback por línea que pinta el progreso de descarga.

    - En terminal (TTY): una sola línea por canción que se reescribe con `\\r`, y salto
      de línea al cambiar de álbum → la consola no se ensucia de infos.
    - Sin TTY (scheduler / `docker logs`): solo loguea la cabecera de cada álbum.
    """
    try:
        is_tty = sys.stdout.isatty()
    except Exception:
        is_tty = False
    state = {"album": None, "n": 0}

    def render(line: str):
        if not line.startswith(PROGRESS_SEP):
            return
        parts = line.split(PROGRESS_SEP)
        if len(parts) < 3:
            return
        album, title = parts[1], parts[2]
        if album != state["album"]:
            if is_tty and state["album"] is not None:
                sys.stdout.write("\n")          # cierra la línea del álbum anterior
            state["album"] = album
            state["n"] = 0
            if is_tty:
                sys.stdout.write(f"💿 {album}\n")
                sys.stdout.flush()
            else:
                logger.info(f"💿 Álbum: {album}")
        state["n"] += 1
        if is_tty:
            try:
                width = shutil.get_terminal_size((100, 20)).columns
            except Exception:
                width = 100
            txt = f"  ⬇ {state['n']:02d}. {title}"
            # recorta y rellena para borrar el resto de la canción anterior
            sys.stdout.write("\r" + txt[: width - 1].ljust(width - 1))
            sys.stdout.flush()

    def finish():
        if is_tty and state["album"] is not None:
            sys.stdout.write("\n")
            sys.stdout.flush()

    render.finish = finish
    return render


def run_yt_dlp(command: list[str]) -> tuple[bool, bool]:
    """
    Ejecuta yt-dlp usando run_subprocess_with_detectors.
    Devuelve (success, critical):
      - success: True si no se detectó ningún error crítico.
      - critical: True si se detectó un error crítico.
    """
    render = _progress_renderer()
    output, (success, critical), detected_error, returncode = run_subprocess_with_detectors(
        command, ERROR_DETECTORS, line_callback=render
    )
    render.finish()

    return success, critical


# Cache temporal en memoria para batch
_batch_cache: Dict[str, Dict] = {}
_disk_cache: Dict[str, Dict] = metadata_cache_load()  # Carga inicial desde json_loader

def save_batch_cache():
    """Guarda en disco las entradas acumuladas en _batch_cache"""
    # No hacer nada si _batch_cache esta vacio
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
    """Comprueba si una URL ya está en la caché de disco."""
    return url in _disk_cache

def fetch_raw_metadata(url: str) -> Dict | None:
    """Obtiene metadatos en bruto de una URL usando yt-dlp, con caché en memoria y disco."""
    global _batch_cache, _disk_cache


    if url in _disk_cache:
        return _disk_cache[url]

    time.sleep(random.uniform(5, 10))

    cmd = [
        "yt-dlp",
        "-j",
        "--skip-download",
        "--js-runtimes", "node",
        "--no-warnings",
        "--sleep-requests", "1.5",
        url
    ]

    if COOKIES_FILE.exists():
        logger.info("Se están usando cookies")
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

    artist = info.get("artists") or info.get("artist") or []
    artist_str = "; ".join(artist) if isinstance(artist, list) else str(artist)


    filtered_info = {
        "id": info.get("id"),
        "title": info.get("title"),
        "artist": artist_str or None,
        "album": info.get("album") or None,
        "date": info.get("release_date") or None,
    }


    _batch_cache[url] = filtered_info
    _disk_cache[url] = filtered_info
    return filtered_info

def flush_batch_cache():
    """Forzar guardado de cualquier batch pendiente"""
    save_batch_cache()
