# app/service/download_service.py
import re
from mutagen.easyid3 import EasyID3
from mutagen.id3 import APIC, ID3, ID3NoHeaderError, error
from src.domain.Metadata import Metadata
from src.infrastructure.config import file_music_extension
from src.infrastructure.system.directory_utils import extract_files, obtener_subcarpetas
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
import time
from src.infrastructure.config.config import now
from src.application.providers.logger_provider import LoggerProvider
from src.utils.audio_utils import extraer_album, obtener_portada_album

logger = LoggerProvider()


def actualizar_portada(songs_files: list[Path], artista: str):
    if not songs_files:
        logger.info(f"[INFO] No hay songs_files para actualizar portada de {artista}")
        return

    primer_mp3 = songs_files[0]
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

    for mp3_file in songs_files:
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


def renombrar_con_indice_en(songs_files: list[Path], artista: str) -> list[Path]:
    renombrados = []
    for i, archivo in enumerate(songs_files, start=1):
        nombre_limpio = re.sub(r"^\d{2}\. ", "", archivo.name)
        nuevo_nombre = f"{i:02d}. {nombre_limpio}"
        nuevo_path = archivo.with_name(nuevo_nombre)

        if archivo != nuevo_path:
            archivo.rename(nuevo_path)
            archivo = nuevo_path  # Actualizar referencia

        actualizar_metadatos_por_defecto(archivo, i, artista)
        renombrados.append(archivo)

    return renombrados


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


def mover_a_albumes(artista_path: Path) -> Dict[str, Path]:
    subcarpetas = [p for p in artista_path.iterdir() if p.is_dir()]
    rutas_album: Dict[str, Path] = {}

    for carpeta in subcarpetas:
        songs_files = sorted(carpeta.glob("*.mp3"))
        if not songs_files:
            continue

        album = extraer_album(songs_files[0])
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

            for mp3 in songs_files:
                destino_mp3 = destino / mp3.name
                if not destino_mp3.exists():
                    mp3.rename(destino_mp3)
            if not any(carpeta.iterdir()):
                carpeta.rmdir()

    return rutas_album



def procesar_albumes(artista_path: Path, options: Optional[dict]=None):
    options = options or {}
    options["filter_by_date"] = options.get("filter_by_date", True)


    mover_a_albumes(artista_path)

    time.sleep(2)
    subcarpetas = obtener_subcarpetas(artista_path)

    for _, ruta in subcarpetas.items():
        songs_files = extract_files(ruta)

        mp3s_a_procesar = filtrar_mp3s_por_fecha(songs_files, now, margen_minutos=5) if options["filter_by_date"] else songs_files
        logger.info(f"🎵 Procesando {len(mp3s_a_procesar)} songs_files en {ruta}")
        if mp3s_a_procesar:
            eliminar_previews(mp3s_a_procesar)
            mp3s_a_procesar = renombrar_con_indice_en(mp3s_a_procesar, artista_path.name)
            actualizar_portada(mp3s_a_procesar, artista_path.name)

def filtrar_mp3s_por_fecha(songs_files: List[Path], referencia_iso: str, margen_minutos: int = 5) -> List[Path]:
    referencia_dt = datetime.fromisoformat(referencia_iso).replace(tzinfo=timezone.utc)
    limite_inferior = referencia_dt - timedelta(minutes=margen_minutos)
    filtrados = []
    for mp3 in songs_files:
        mtime = datetime.fromtimestamp(mp3.stat().st_mtime, tz=timezone.utc)
        if mtime >= limite_inferior:
            filtrados.append(mp3)
    return filtrados


def actualizar_metadatos_por_defecto(archivo: Path, numero: int, artista: str) -> Path:
    try:
        audio = EasyID3(archivo)
    except ID3NoHeaderError:
        audio = EasyID3()

    audio["tracknumber"] = str(numero)
    audio["albumartist"] = artista
    audio["artist"] = artista.replace(",", ";")
    if not audio.get("album"):
        audio["album"] = archivo.parent.name
    audio.save(archivo)
    return archivo

def extract_metadata(raw_metadata: Dict[str, Any], fields: List[str]) -> Metadata:
        """
        Recibe metadatos crudos y una lista de campos a extraer.
        Devuelve un objeto Metadata con solo los campos solicitados rellenados.
        """
        if not raw_metadata:
            return Metadata()  # Retorna un objeto vacío si no hay metadatos

        # Creamos un diccionario con solo los campos disponibles en raw_metadata
        data_for_model = {}
        for field in fields:
            # Adaptamos nombres si el raw_metadata usa otro casing
            value = raw_metadata.get(field.lower()) or raw_metadata.get(field)
            if value is not None:
                data_for_model[field] = value

        # Inicializamos el modelo Metadata usando **kwargs
        return Metadata(**data_for_model)