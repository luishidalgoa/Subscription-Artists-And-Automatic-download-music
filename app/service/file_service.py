# app/service/file_service.py
from pathlib import Path
from app.utils.audio_utils import extraer_album
import logging
logger = logging.getLogger(__name__)

import re
from typing import Dict
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3NoHeaderError

def mover_a_albumes(artista_path: Path) -> Dict[str, Path]:
    subcarpetas = [p for p in artista_path.iterdir() if p.is_dir()]
    rutas_album: Dict[str, Path] = {}

    for carpeta in subcarpetas:
        mp3s = sorted(carpeta.glob("*.mp3"))
        if not mp3s:
            continue

        album = extraer_album(mp3s[0])
        if not album:
            continue

        album = album.strip()
        destino = artista_path / album
        rutas_album[album] = destino

        if carpeta.name != album:
            destino.mkdir(exist_ok=True)
            for mp3 in mp3s:
                destino_mp3 = destino / mp3.name
                if not destino_mp3.exists():
                    mp3.rename(destino_mp3)
            if not any(carpeta.iterdir()):
                carpeta.rmdir()

        # Actualizar metadatos de todos los mp3 del álbum
        #actualizar_metadatos_album(destino)

    return rutas_album

def eliminar_previews(artista_path: Path):
    previews = list(artista_path.glob("**/*(Preview)*.mp3"))
    for archivo in previews:
        try:
            archivo.unlink()
            carpeta = archivo.parent
            if not any(carpeta.iterdir()):
                carpeta.rmdir()
        except Exception as e:
            logger.error(f"Error al eliminar {archivo.name}: {e}")

def renombrar_con_indice_en(mp3s: Path, artista: str):

    for i, archivo in enumerate(mp3s, start=1):
        # Limpiar nombre: quitar si empieza por "##. "
        nombre_limpio = re.sub(r"^\d{2}\. ", "", archivo.name)
        nuevo_nombre = f"{i:02d}. {nombre_limpio}"
        nuevo_path = archivo.with_name(nuevo_nombre)

        # Renombrar si es necesario
        if archivo != nuevo_path:
            archivo.rename(nuevo_path)
            archivo = nuevo_path  # Actualizar referencia

        # Actualizar metadatos
        actualizar_metadatos_por_defecto(archivo, i,artista)


def actualizar_metadatos_por_defecto(archivo: Path, numero: int, artista: str):
    try:
        audio = EasyID3(archivo)
    except ID3NoHeaderError:
        audio = EasyID3()

    # imprimimos el title del archivo
    logger.info(f"Archivo de musica: {archivo.name}")
    
    audio["tracknumber"] = str(numero)
    #interprete del album
    audio["albumartist"] = artista
    audio.save(archivo)
    
"""
def actualizar_metadatos_album(album_path: Path):
    mp3s = sorted(album_path.glob("*.mp3"))
    if not mp3s:
        return

    primer_mp3 = mp3s[0]

    try:
        audio = EasyID3(primer_mp3)
        title = audio.get("title", [""])[0]
        artist = audio.get("albumartist", [""])[0]
        portada = obtener_portada_album(title, artist)
    except Exception as e:
        logger.warning(f"[WARN] No se pudo obtener portada: {e}")
        portada = None

    for mp3 in mp3s:
        datos = consultar_metadatos(mp3)
        actualizar_metadatos(mp3, datos, portada)
"""