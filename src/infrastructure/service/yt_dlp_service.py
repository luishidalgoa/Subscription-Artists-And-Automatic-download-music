# app/service/console.reader.service.py
import json
from os import replace
import random
import subprocess
import time
from typing import Dict
from src.application.providers.logger_provider import LoggerProvider
from src.infrastructure.config.config import COOKIES_FILE, METADATA_SONGS_CACHE
from src.infrastructure.filesystem.json_loader import metadata_cache_load

logger= LoggerProvider()

def run_yt_dlp(command: list[str]) -> bool:
    """
    Ejecuta yt-dlp y pasa cada línea por los detectores de errores.
    Devuelve True si no se detectó ningún error crítico,
    False si hubo que abortar.
    """
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,      # 👈 sin esto process.stdout será None
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )


    error_detected = False
    for line in process.stdout:
        line = line.strip()
        if line:
            logger.debug(f"[yt-dlp] {line}")

            # Detectar descarga completada
            if line.startswith("[ExtractAudio] Destination:") or "has already been downloaded" in line:
                # extraer el nombre del archivo
                title = line.split("Destination:")[-1].strip() if "Destination:" in line else line
                logger.info(f"🎵 Descargado: {title}")

        # probar cada detector
        for detector in ERROR_DETECTORS:
            if detector(line):  # si detecta error, abortamos
                error_detected = True
                process.terminate()
                process.wait()
                break

        if error_detected:
            break

    process.wait()

    return not error_detected


def detect_ip_ban(line: str) -> bool:
    patterns = [
        "Sign in to confirm you’re not a bot",
        "Sign in to confirm you're not a bot",
        "Use --cookies-from-browser or --cookies for the authentication"
    ]
    if any(p in line for p in patterns):
        logger.error("🚫 YouTube ha bloqueado temporalmente la IP (captcha / bot check).")
        return True
    return False

ERROR_DETECTORS = [
    detect_ip_ban,
]

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

def fetch_raw_metadata(url: str) -> Dict:
    """
    Obtiene metadatos de YouTube usando 'yt-dlp', con:
      - Pausa aleatoria entre 5 y 10 segundos.
      - Cookies desde COOKIES_FILE.
      - Cache persistente.
      - Solo devuelve los campos: 'artists', 'album', 'title', 'id'
    """
    global _batch_cache, _disk_cache

    # Revisar cache en disco
    if url in _disk_cache:
        return _disk_cache[url]

    # Pausa aleatoria entre 5-10 segundos
    wait_time = random.uniform(5, 10)
    time.sleep(wait_time)

    # Preparar comando
    cmd = ["yt-dlp", "-j", "--skip-download", url]

    # Añadir cookies si existe el archivo
    if COOKIES_FILE.exists():
        cmd += ["--cookies", str(COOKIES_FILE)]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        info = json.loads(result.stdout)
        artists_list = info.get("artists") or info.get("artist") or []
        if isinstance(artists_list, list):
            artist_str = "; ".join(artists_list)
        else:
            artist_str = str(artists_list)

        logger.info(f"Artistas: {artist_str}")

        # Extraer solo los campos deseados
        filtered_info = {
            "id": info.get("id"),
            "title": info.get("title"),
            "album": info.get("album"),
            "year": info.get("release_date"),
            "artist": artist_str
        }

        # Guardar en cache
        _batch_cache[url] = filtered_info
        _disk_cache[url] = filtered_info

        return filtered_info

    except subprocess.CalledProcessError as e:
        logger.error(f"[yt-dlp] Error ejecutando yt-dlp para {url}: {e.stderr}")
        raise RuntimeError(f"Error ejecutando yt-dlp: {e.stderr}") from e

    except json.JSONDecodeError as e:
        logger.error(f"[yt-dlp] Salida inválida de yt-dlp para {url}")
        raise RuntimeError(f"Salida inválida de yt-dlp para {url}") from e

    except Exception as e:
        logger.error(f"[yt-dlp] Error inesperado para {url}: {e}")
        raise

def flush_batch_cache():
    """Forzar guardado de cualquier batch pendiente"""
    save_batch_cache()