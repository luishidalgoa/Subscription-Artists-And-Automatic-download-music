from os import mkdir
from re import A
import shutil
from src.application.providers.logger_provider import LoggerProvider
from src.domain.Metadata import Metadata
from src.domain.base_command import BaseCommand
from src.infrastructure.audio.handler_factory import AudioHandlerFactory
from src.infrastructure.config.config import COOKIES_FILE, MUSIC_ROOT_PATH, TEMP_MUSIC_PATH
from src.infrastructure.service import album_postprocessor, yt_dlp_service
from pathlib import Path

from src.infrastructure.system.directory_utils import extract_files
from src.utils.Transform import Transform


logger = LoggerProvider()
DESCRIPCION = "Descarga canciones a partir de una URL"
class DownloadCommand(BaseCommand):
    DESCRIPCION = DESCRIPCION
    ARGUMENTOS = {
        "--url": {
            "params": {
                "required": True,
                "help": "URL de la canción o playlist a descargar",
            }
        },
        "--artist": {
            "params": {
                "required": False,
                "help": "Nombre del artista (opcional, para metadatos)",
            }
        },
    }
    def handle(self, parsed_args):
        artist: str = Transform.sanitize_path_component(parsed_args.artist) if parsed_args.artist else None
        if not parsed_args.url:
            raise ValueError("La URL es obligatoria")
        url = parsed_args.url

        temp_output_path = str(TEMP_MUSIC_PATH / "%(title)s.%(ext)s")


        cmd = [
                "yt-dlp",
                "--cookies", str(COOKIES_FILE),
                "--quiet",
                "--extract-audio",
                "--audio-format", "mp3",
                "--no-overwrites",
                "--add-metadata",
                "--embed-thumbnail",
                "--sleep-interval", "5",
                "--max-sleep-interval", "10",
                "--break-on-reject",
                "-o", temp_output_path, url
        ]

        success = yt_dlp_service.run_yt_dlp(cmd) 

        if not success:
            logger.error("La descarga falló o no se encontraron nuevos archivos.")
            return

        files = extract_files(TEMP_MUSIC_PATH)
        album_postprocessor.renombrar_con_indice_en(files)

        first:bool = True
        album_name:str = None

        for song in files:
            audio_ext = str(song.suffix).rsplit(".", 1)[-1].lower()
            handler = AudioHandlerFactory().get_handler(audio_ext)
            try:
                comment = handler.extract_comment(str(song))
                if not comment:
                    logger.warning(f"No hay URL de YouTube en el archivo: {song}")
                    continue
                raw_metadata = yt_dlp_service.fetch_raw_metadata(comment)

                tags_to_extract = list(vars(Metadata()).keys())
                tags_to_extract.remove("Album")
                metadata_obj = album_postprocessor.extract_metadata(raw_metadata, tags_to_extract)

                if not artist:
                     artist = Transform.sanitize_path_component(metadata_obj.Artist)

                if first:
                     first = False
                     album_postprocessor.actualizar_portada(files,artist)

                     album_name = Transform.sanitize_path_component(handler.getMetadata(song,["Album"]).Album)

                     #comprobamos que existe en /music/ un artista con el mismo nombre
                     for artist in MUSIC_ROOT_PATH.iterdir():
                        if artist.is_dir() and artist.name.lower() == metadata_obj.Artist.lower():
                            artist = artist.name
                            break
                            

                #debe abrirse despues de actualizar portada por que si no, sobreescribe la portada nueva por la antigua
                audio = handler.open_file(str(song))
                handler.apply_metadata(audio, metadata_obj, tags_to_extract, artist=artist)
                audio.save()
            except Exception as e:
                    yt_dlp_service.flush_batch_cache()
                    logger.error(f"Error procesando archivo {song}: {e}")
        
        #mover a carpeta artista. creando la carpeta del album
        final_path = MUSIC_ROOT_PATH / artist / album_name
        #creamos la carpeta del album si no existe dentro del artista
        if album_name:
            final_path.mkdir(parents=True, exist_ok=True)
            for song in files:
                destino = final_path / song.name
                if not destino.exists():
                    shutil.move(str(song), str(destino))
                else:
                    logger.info(f"El archivo {destino} ya existe, se omite mover.")
        
        
        
