# app/utils/audio_utils.py
from mutagen.easyid3 import EasyID3
import requests
from typing import Optional
import mutagen
from pathlib import Path
import re
import unicodedata
from src.application.providers.logger_provider import LoggerProvider

logger = LoggerProvider()

def extraer_album(mp3_path: str) -> str | None:
    try:
        tags = EasyID3(mp3_path)
        return tags.get("album", [None])[0]
    except Exception:
        return None


def buscar_resultados_deezer(query: str) -> list[dict]:
    query_normalized = normalize_to_ascii(query)
    url = f"https://api.deezer.com/search/album?q={requests.utils.quote(query_normalized)}"
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
    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            return resp.content
        logger.warning("[WARN] Fallo al descargar imagen desde Deezer (%s) - status %s", url, resp.status_code)
    except Exception as e:
        logger.error("[ERROR] Fallo al descargar imagen: %s", e)
    return None

def extraer_tags(mp3: Path) -> dict[str, str]:
    audio = mutagen.File(mp3)
    def get_tag(keys):
        for k in keys:
            val = audio.tags.get(k)
            if val:
                if isinstance(val, (list, tuple)):
                    return str(val[0])
                return str(val)
        return ""
    return {
        "albumartist": get_tag(['TPE2', 'albumartist']),
        "artist": get_tag(['TPE1', 'artist']),
        "title": get_tag(['TIT2', 'title']),
        "album": get_tag(['TALB', 'album']),
    }

def _artista_coincide(albumartist_api: str, artist_api: str, albumartist_mp3: str, artist_mp3: str) -> bool:
    """
    Valida si el artista del API Deezer coincide con albumartist o alguno de los artistas (separados por coma) del mp3.
    """
    albumartist_api = albumartist_api.casefold()
    artist_api = artist_api.casefold()
    albumartist_mp3 = albumartist_mp3.casefold()
    artist_mp3 = artist_mp3.casefold()

    # Primero compara con albumartist
    if albumartist_api == albumartist_mp3:
        return True
    # Si falla, separa artist_mp3 por coma y compara con cada uno
    artistas = [a.strip() for a in artist_mp3.split(",")]
    if artist_api in artistas:
        return True
    return False

def normalize_to_ascii(s: str) -> str:
    s = unicodedata.normalize('NFD', s)
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    replacements = {
        '’': "'",
        '‘': "'",
        '“': '"',
        '”': '"',
        '：': ':',
        '–': '-',
        '—': '-',
        '…': '...',
        '´': "'",
        '¨': '"',
    }
    for orig, repl in replacements.items():
        s = s.replace(orig, repl)
    s = re.sub(r'[^\x00-\x7F]', '', s)  # eliminar no ASCII restantes
    s = re.sub(r'\s+', ' ', s).strip()
    return s


def obtener_portada_album(mp3: Path) -> Optional[bytes]:
    tags = extraer_tags(mp3)
    albumartist = normalize_to_ascii(tags['albumartist'])
    artist = normalize_to_ascii(tags['artist'])
    title = normalize_to_ascii(tags['title'])
    album = normalize_to_ascii(tags['album'])

    if not album or not artist:
        logger.warning(f"[WARN] El archivo {mp3} no tiene tags de artista o álbum suficientes")
        return None

    albumartist_norm = albumartist.casefold()
    artist_norm = artist.casefold()
    title_norm = title.casefold()
    album_norm = album.casefold()

    logger.info(f"[INFO] Buscando portada para: {albumartist} - {album}")

    # 1) Búsqueda amplia
    query = f'?q=artist:"{albumartist}" album:"{album}"'
    resultados = buscar_resultados_deezer(query)

    for entry in resultados:
        if "cover_xl" in entry or entry.get("type") == "album":
            artista_api = normalize_to_ascii(entry.get("artist", {}).get("name", "")).casefold()
            nombre_album_api = normalize_to_ascii(entry.get("title", "")).casefold()
            portada_url = (
                entry.get("cover_xl")
                or entry.get("cover_big")
                or entry.get("cover_medium")
            )
        elif "album" in entry:
            artista_api = normalize_to_ascii(entry.get("artist", {}).get("name", ""))
            if not artista_api:
                artista_api = normalize_to_ascii(entry.get("album", {}).get("artist", {}).get("name", ""))
            artista_api = artista_api.casefold()

            nombre_album_api = normalize_to_ascii(entry.get("album", {}).get("title", "")).casefold()
            portada_url = (
                entry.get("album", {}).get("cover_xl")
                or entry.get("album", {}).get("cover_big")
                or entry.get("album", {}).get("cover_medium")
            )
        else:
            continue

        def normalize_str(s: str) -> str:
            s = s.casefold()
            s = unicodedata.normalize('NFD', s)
            s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
            s = re.sub(r'\s+', ' ', s).strip()
            return s

        nombre_album_api_norm = normalize_str(nombre_album_api)
        album_norm_norm = normalize_str(album_norm)

        if _artista_coincide(
        albumartist_api=artista_api,
        artist_api=artista_api,
        albumartist_mp3=albumartist_norm,
        artist_mp3=artist_norm
        ) and portada_url:
            img = _download_image(portada_url)
            if img:
                return img

    # 2) Búsqueda estricta con validación flexible de artista
    query = f'album?q=artist:"{albumartist}" album:"{album}"'
    resultados = buscar_resultados_deezer(query)

    for entry in resultados:
        if "cover_xl" in entry or entry.get("type") == "album":
            artista_api = normalize_to_ascii(entry.get("artist", {}).get("name", "")).casefold()
            nombre_album_api = normalize_to_ascii(entry.get("title", "")).casefold()
            portada_url = (
                entry.get("cover_xl")
                or entry.get("cover_big")
                or entry.get("cover_medium")
            )
        elif "album" in entry:
            artista_api = normalize_to_ascii(entry.get("artist", {}).get("name", ""))
            if not artista_api:
                artista_api = normalize_to_ascii(entry.get("album", {}).get("artist", {}).get("name", ""))
            artista_api = artista_api.casefold()

            nombre_album_api = normalize_to_ascii(entry.get("album", {}).get("title", "")).casefold()
            portada_url = (
                entry.get("album", {}).get("cover_xl")
                or entry.get("album", {}).get("cover_big")
                or entry.get("album", {}).get("cover_medium")
            )
        else:
            continue

        def normalize_str(s: str) -> str:
            s = s.casefold()
            s = unicodedata.normalize('NFD', s)
            s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
            s = re.sub(r'\s+', ' ', s).strip()
            return s

        nombre_album_api_norm = normalize_str(nombre_album_api)
        album_norm_norm = normalize_str(album_norm)

        if _artista_coincide(
        albumartist_api=artista_api,
        artist_api=artista_api,
        albumartist_mp3=albumartist_norm,
        artist_mp3=artist_norm
        ) and portada_url:
            img = _download_image(portada_url)
            if img:
                return img

    # 3) Último intento: comparar sin normalizar (o ya ascii y casefold)
    if resultados:
        for entry in resultados:
            nombre_album_api = ""
            portada_url = None
            if "cover_xl" in entry or entry.get("type") == "album":
                nombre_album_api = normalize_to_ascii(entry.get("title", "")).casefold()
                portada_url = (
                    entry.get("cover_xl")
                    or entry.get("cover_big")
                    or entry.get("cover_medium")
                )
            elif "album" in entry:
                nombre_album_api = normalize_to_ascii(entry.get("album", {}).get("title", "")).casefold()
                portada_url = (
                    entry.get("album", {}).get("cover_xl")
                    or entry.get("album", {}).get("cover_big")
                    or entry.get("album", {}).get("cover_medium")
                )
                
            if portada_url:
                img = _download_image(portada_url)
                if img:
                    return img

    return None