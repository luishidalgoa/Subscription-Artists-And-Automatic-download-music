# app/utils/audio_utils.py
from mutagen.easyid3 import EasyID3
import logging
logger = logging.getLogger(__name__)
import requests
from typing import Optional

def extraer_album(mp3_path: str) -> str | None:
    try:
        tags = EasyID3(mp3_path)
        return tags.get("album", [None])[0]
    except Exception:
        return None


def buscar_resultados_deezer(query: str) -> list[dict]:
    """
    Hace la búsqueda en Deezer y devuelve la lista de tracks (diccionarios).
    """
    url = f"https://api.deezer.com/search?q={requests.utils.quote(query)}"
    logger.info(f"[INFO] Buscando en Deezer: {url}")
    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code != 200:
            logger.warning(f"[WARN] Deezer API respondió con status {resp.status_code}")
            return []
        data = resp.json()
        return data.get("data", [])
    except Exception as e:
        logger.error(f"[ERROR] Fallo al buscar en Deezer: {e}")
        return []

def _download_image(url: str) -> Optional[bytes]:
    """Descarga una imagen y devuelve los bytes o None en caso de error."""
    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            return resp.content
        logger.warning("[WARN] Fallo al descargar imagen desde Deezer (%s) - status %s", url, resp.status_code)
    except Exception as e:
        logger.error("[ERROR] Fallo al descargar imagen: %s", e)
    return None


def obtener_portada_album(title: str, artist: str, album: str) -> bytes | None:
    """
    Busca la portada del álbum usando la API pública de Deezer.

    Estrategia:
    1) Búsqueda amplia: `artist title album` -> buscar en resultados (pueden ser tracks o albums).
    2) Si no hay coincidencias, intento estricto: `artist:"{artist}" album:"{album}"`.

    Devuelve los bytes de la imagen o None.
    """
    artist_norm = artist.strip().casefold()
    title_norm = title.strip().casefold()
    album_norm = album.strip().casefold()

    # ------------------ 1) Búsqueda amplia: artist + title + album ------------------
    query = f"{artist} {title} {album}"
    resultados = buscar_resultados_deezer(query)

    for entry in resultados:
        # Si es un track (resultado del /search normal), contiene una clave 'album'
        if "album" in entry:
            artista = entry.get("artist", {}).get("name", "").strip().casefold()
            cancion = entry.get("title", "").strip().casefold()
            nombre_album = entry.get("album", {}).get("title", "").strip().casefold()
            portada_url = (
                entry.get("album", {}).get("cover_xl")
                or entry.get("album", {}).get("cover_big")
                or entry.get("album", {}).get("cover_medium")
            )
        else:
            # Posible objeto album (p.ej. devuelto por /search? q=artist:"..." album:"..."), tiene portada en raíz
            artista = entry.get("artist", {}).get("name", "").strip().casefold()
            cancion = ""
            nombre_album = entry.get("title", "").strip().casefold()
            portada_url = (
                entry.get("cover_xl")
                or entry.get("cover_big")
                or entry.get("cover_medium")
            )

        if (
            artista == artist_norm
            and cancion == title_norm
            and nombre_album == album_norm
            and portada_url
        ):
            img = _download_image(portada_url)
            if img:
                return img

    # ------------------ 2) Intento estricto: artist:"..." album:"..." ------------------
    query = f'artist:"{artist}" album:"{album}"'
    resultados = buscar_resultados_deezer(query)

    for entry in resultados:
        # Caso: entrada de tipo album (portada en la raiz)
        if "cover_xl" in entry or entry.get("type") == "album":
            artista = entry.get("artist", {}).get("name", "").strip().casefold()
            nombre_album = entry.get("title", "").strip().casefold()
            portada_url = (
                entry.get("cover_xl")
                or entry.get("cover_big")
                or entry.get("cover_medium")
            )
        # Caso: entrada de tipo track (tiene campo 'album')
        elif "album" in entry:
            artista = entry.get("artist", {}).get("name", "").strip().casefold()
            nombre_album = entry.get("album", {}).get("title", "").strip().casefold()
            portada_url = (
                entry.get("album", {}).get("cover_xl")
                or entry.get("album", {}).get("cover_big")
                or entry.get("album", {}).get("cover_medium")
            )
        else:
            continue

        if artista == artist_norm and nombre_album == album_norm and portada_url:
            img = _download_image(portada_url)
            if img:
                return img

    logger.warning("[WARN] No se encontró portada para '%s' de '%s' en álbum '%s'", title, artist, album)
    return None