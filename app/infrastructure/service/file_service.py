# app/service/file_service.py
from pathlib import Path
from app.utils.audio_utils import extraer_album, obtener_portada_album
from mutagen.id3 import ID3, APIC, error

import re
from typing import Dict
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3NoHeaderError
from app.application.providers.logger_provider import LoggerProvider

logger = LoggerProvider()

def obtener_subcarpetas(directorio: Path) -> dict[str, Path]:
    """
    Devuelve un diccionario {nombre_carpeta: Path} con las subcarpetas directas.
    """
    return {carpeta.name: carpeta for carpeta in directorio.iterdir() if carpeta.is_dir()}

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
            try:
                # Esto crea la carpeta destino y todas las carpetas padre si no existen
                destino.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                # Aquí podrías loguear el error o levantarlo si quieres
                print(f"Error creando carpeta {destino}: {e}")
                continue  # Salta al siguiente álbum para no detener todo

            for mp3 in mp3s:
                destino_mp3 = destino / mp3.name
                if not destino_mp3.exists():
                    mp3.rename(destino_mp3)
            if not any(carpeta.iterdir()):
                carpeta.rmdir()

    return rutas_album


def eliminar_previews(archivos_mp3: list[Path]):
    for archivo in archivos_mp3:
        # Solo actuar si el nombre contiene "(Preview)"
        if "(Preview)" in archivo.name:
            try:
                archivo.unlink()  # Elimina el archivo
                carpeta = archivo.parent
                # Si la carpeta queda vacía, la borra
                if not any(carpeta.iterdir()):
                    carpeta.rmdir()
            except Exception as e:
                logger.error(f"Error al eliminar {archivo.name}: {e}")

def renombrar_con_indice_en(mp3s: list[Path], artista: str) -> list[Path]:
    renombrados = []
    for i, archivo in enumerate(mp3s, start=1):
        nombre_limpio = re.sub(r"^\d{2}\. ", "", archivo.name)
        nuevo_nombre = f"{i:02d}. {nombre_limpio}"
        nuevo_path = archivo.with_name(nuevo_nombre)

        if archivo != nuevo_path:
            archivo.rename(nuevo_path)
            archivo = nuevo_path  # Actualizar referencia

        actualizar_metadatos_por_defecto(archivo, i, artista)
        renombrados.append(archivo)

    return renombrados


def actualizar_metadatos_por_defecto(archivo: Path, numero: int, artista: str) -> Path:
    try:
        audio = EasyID3(archivo)
    except ID3NoHeaderError:
        audio = EasyID3()

    audio["tracknumber"] = str(numero)
    audio["albumartist"] = artista
    if not audio.get("album"):
        audio["album"] = archivo.parent.name
    audio.save(archivo)
    return archivo

    

def actualizar_portada(mp3s: list[Path], artista: str):
    if not mp3s:
        logger.info(f"[INFO] No hay mp3s para actualizar portada de {artista}")
        return

    primer_mp3 = mp3s[0]
    album = primer_mp3.parent.name

    try:
        audio_easy = EasyID3(primer_mp3)
        title = audio_easy.get("title", [""])[0]
        artist_tag = audio_easy.get("albumartist", [""])[0] or artista
    
        portada_bytes = obtener_portada_album(primer_mp3)
        if not portada_bytes:
            logger.warning(f"[WARN] No se encontró portada para '{title}' de '{artist_tag}' en álbum '{album}'")
            return

    except Exception as e:
        logger.warning(f"[WARN] No se pudo obtener portada: {e}")
        return

    for mp3_file in mp3s:
        try:
            audio = ID3(mp3_file)
        except error:
            audio = ID3()  # Si no tiene tags previas

        audio.delall("APIC")
        audio.add(
            APIC(
                encoding=3,
                mime="image/jpeg",
                type=3,
                desc="Cover",
                data=portada_bytes
            )
        )
        audio.save(mp3_file)
        logger.info(f"[INFO] Portada actualizada en {mp3_file.name}")

