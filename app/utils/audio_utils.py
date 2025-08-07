from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, APIC, ID3NoHeaderError
from typing import Dict
from pathlib import Path
import logging
logger = logging.getLogger(__name__)

def extraer_album(mp3_path: str) -> str | None:
    try:
        tags = EasyID3(mp3_path)
        return tags.get("album", [None])[0]
    except Exception:
        return None
"""
def consultar_metadatos(mp3_path: Path) -> Dict:
    try:
        audio = EasyID3(mp3_path)
        title = audio.get("title", [""])[0]
        artist = audio.get("albumartist", [""])[0]
        album = audio.get("album", [""])[0]

        logger.info("Metadatos leídos: title=%s, artist=%s, album=%s", title, artist, album)

    except Exception as e:
        logger.error(f"[ERROR] No se pudieron leer metadatos: {e}")
        return {}

    if not title or not artist or not album:
        logger.warning("Metadatos insuficientes para búsqueda")
        return {}

    try:
        # 🔍 Búsqueda más concreta con título, artista y álbum
        result = musicbrainzngs.search_recordings(
            recording=title,
            artist=artist,
            release=album,
            limit=3
        )

        # 🔎 Imprimir resultado completo para depuración
        logger.info("Resultado completo de búsqueda MusicBrainz: %s", result)

        recordings = result.get("recording-list", [])
        if not recordings:
            logger.warning(f"No se encontraron grabaciones en MusicBrainz para: {title} - {artist} ({album})")
            return {}

        recording = recordings[0]
        release = recording.get("release-list", [{}])[0]
        release_id = release.get("id")
        tags = recording.get("tag-list", [])
        genre = tags[0]["name"] if tags else None

        portada = None
        if release_id:
            try:
                portada = musicbrainzngs.get_image_front(release_id)
            except musicbrainzngs.ResponseError:
                logger.warning("No se pudo obtener portada para release_id=%s", release_id)

        logger.info("🎵 Género: %s, Portada: %s", genre or "Desconocido", "Disponible" if portada else "No disponible")

        return {
            "genero": genre,
            "portada": portada
        }

    except Exception as e:
        logger.error(f"[ERROR] Fallo al consultar MusicBrainz: {e}")
        return {}


def actualizar_metadatos(mp3_path: Path, datos: Dict, portada: bytes = None):
    try:
        audio = EasyID3(mp3_path)
    except ID3NoHeaderError:
        audio = EasyID3()

    if "genero" in datos and datos["genero"]:
        audio["genre"] = datos["genero"]
    audio.save(mp3_path)

    if portada:
        try:
            audio_id3 = ID3(mp3_path)
            audio_id3.delall("APIC")  # Quitar portada anterior
            audio_id3.add(APIC(
                encoding=3, mime='image/jpeg', type=3, desc=u'Cover',
                data=portada
            ))
            audio_id3.save(mp3_path)
        except Exception as e:
            logger.error(f"[ERROR] No se pudo actualizar la portada: {e}")

def obtener_portada_album(title: str, artist: str) -> bytes | None:
    try:
        result = musicbrainzngs.search_recordings(
            recording=title, artist=artist, limit=1
        )
        recordings = result.get("recording-list", [])
        if not recordings:
            return None

        release = recordings[0].get("release-list", [{}])[0]
        release_id = release.get("id")
        if not release_id:
            return None

        return musicbrainzngs.get_image_front(release_id)

    except Exception as e:
        logger.error(f"[ERROR] Fallo al obtener portada del álbum: {e}")
        return None
"""