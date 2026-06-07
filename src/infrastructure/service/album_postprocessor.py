# app/service/download_service.py
import re
from mutagen.easyid3 import EasyID3
from mutagen.id3 import APIC, ID3, ID3NoHeaderError, error
from pathlib import Path
from typing import Union, List
from src.domain.Metadata import Metadata
from src.infrastructure.config import file_music_extension
from src.infrastructure.system.directory_utils import extract_files, obtener_subcarpetas
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
import time
from src.infrastructure.config import config as app_config
from src.application.providers.logger_provider import LoggerProvider
from src.utils.audio_utils import extraer_album, obtener_portada_album

logger = LoggerProvider()


def actualizar_portada(songs_files: list[Path], artista: str):
    if not songs_files:
        logger.info(f"[INFO] No hay songs_files para actualizar portada de {artista}")
        return

    primer_mp3 = songs_files[0]

    try:
        audio_easy = EasyID3(primer_mp3)
        title = audio_easy.get("title", [""])[0]
        artist_tag = audio_easy.get("albumartist", [""])[0] or artista
        album = audio_easy.get("album", [""])[0]

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


# Prefijo numérico ya existente en el nombre (p.ej. "01. ", "00007. ") para poder
# normalizarlo a 1..N por álbum sin acumular prefijos en sucesivas pasadas.
_TRACK_PREFIX_RE = re.compile(r"^\d+\.\s+")


def actualizar_indice_pista(songs_files: list[Path]) -> list[Path]:
    """Fija el tag tracknumber (1..N) y renombra el fichero con prefijo limpio "NN. ".

    `songs_files` viene ordenado por nombre (extract_files), y como la descarga deja un
    prefijo numérico zero-padded, ese orden == orden real del álbum. Aquí se reescribe a
    un índice contiguo por-álbum, tanto en el tag como en el nombre de fichero, de modo
    que Topic y releases queden consistentes (1..N) y Navidrome los muestre en orden.
    """
    renombrados = []
    for i, archivo in enumerate(songs_files, start=1):
        try:
            audio = EasyID3(archivo)
        except ID3NoHeaderError:
            audio = EasyID3()

        audio["tracknumber"] = str(i)
        audio.save(archivo)

        # Renombrar a "NN. <título sin prefijo previo>" (idempotente: si ya está bien, no toca).
        base = _TRACK_PREFIX_RE.sub("", archivo.name)
        destino = archivo.with_name(f"{i:02d}. {base}")
        if destino != archivo and not destino.exists():
            archivo.rename(destino)
            archivo = destino

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



def procesar_album(album_path: Path, options: Optional[dict] = None):
    """Post-procesa UN álbum (una carpeta): previews, índice de pista, metadatos y portada.

    Pensado para invocarse en cuanto un álbum termina de descargarse (no al final del
    artista). Con `filter_by_date` (por defecto True) solo toca los archivos recién bajados.
    """
    options = options or {}
    options["filter_by_date"] = options.get("filter_by_date", True)

    songs_files = extract_files(album_path)
    if not songs_files:
        return

    mp3s_a_procesar = (
        filtrar_mp3s_por_fecha(songs_files, app_config.now, margen_minutos=5)
        if options["filter_by_date"] else songs_files
    )
    if not mp3s_a_procesar:
        return

    logger.info(f"🎵 Procesando {len(mp3s_a_procesar)} songs_files en {album_path}")
    eliminar_previews(mp3s_a_procesar)
    mp3s_a_procesar = actualizar_indice_pista(mp3s_a_procesar)
    mp3s_a_procesar = actualizar_metadatos_por_defecto(mp3s_a_procesar)
    # El artista es la carpeta padre del álbum.
    actualizar_portada(mp3s_a_procesar, album_path.parent.name)


def procesar_albumes(artista_path: Path, options: Optional[dict]=None):
    """Post-procesa TODOS los álbumes de un artista (delegando en procesar_album)."""
    options = options or {}
    options["filter_by_date"] = options.get("filter_by_date", True)

    time.sleep(2)
    subcarpetas = obtener_subcarpetas(artista_path)

    for _, ruta in subcarpetas.items():
        procesar_album(ruta, options)

def filtrar_mp3s_por_fecha(songs_files: List[Path], referencia_iso: str, margen_minutos: int = 5) -> List[Path]:
    referencia_dt = datetime.fromisoformat(referencia_iso).replace(tzinfo=timezone.utc)
    limite_inferior = referencia_dt - timedelta(minutes=margen_minutos)
    filtrados = []
    for mp3 in songs_files:
        mtime = datetime.fromtimestamp(mp3.stat().st_mtime, tz=timezone.utc)
        if mtime >= limite_inferior:
            filtrados.append(mp3)
    return filtrados


def actualizar_metadatos_por_defecto(archivo: Union[Path, List[Path]]) -> Union[Path, List[Path]]:
    """Actualiza metadatos por defecto en uno o varios archivos MP3. modifica 'albumartist', 'artist' y 'album'."""
    archivos = [archivo] if isinstance(archivo, Path) else archivo

    for f in archivos:
        try:
            try:
                audio = EasyID3(f)
            except ID3NoHeaderError:
                audio = EasyID3()
            
            # Album artist: carpeta padre del artista
            if f.parent.parent and f.parent.parent.name:
                audio["albumartist"] = f.parent.parent.name
            else:
                audio["albumartist"] = "Unknown Artist"
            
            # Artist: reemplazar comas por ;
            if "artist" in audio and audio["artist"]:
                artist = "; ".join(audio["artist"])
                artist = artist.replace(",", ";")
                audio["artist"] = [artist]
            else:
                artist_name = f.parent.parent.name if f.parent.parent else "Unknown Artist"
                audio["artist"] = [artist_name]
            
            # Album: forzar el nombre de la carpeta final, aunque yt-dlp haya escrito otro valor
            audio["album"] = f.parent.name if f.parent.name else "Unknown Album"
            
            audio.save(f)
        except Exception as e:
            print(f"Error actualizando metadatos de {f}: {e}")

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
