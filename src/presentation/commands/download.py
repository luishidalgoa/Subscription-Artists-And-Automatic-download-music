import json
from os import mkdir
from re import A
import shutil
import subprocess
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
DESCRIPCION = "Descarga canciones a partir de una URL de Youtube MUSIC"
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

        # Detectar playlist
        is_playlist = "list=" in url

        playlist_title = None

        if is_playlist:
            # 🔥 Sacamos el título REAL de la playlist
            cmd_info = [
                "yt-dlp",
                "--cookies", str(COOKIES_FILE),
                "--dump-single-json",
                url
            ]

            result = subprocess.run(cmd_info, capture_output=True, text=True)
            data = json.loads(result.stdout)

            playlist_title = data.get("title")

        temp_output_path = str(TEMP_MUSIC_PATH / "%(autonumber)02d. %(title)s.%(ext)s")

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
            "-o", temp_output_path,
            url
        ]

        success, critical = yt_dlp_service.run_yt_dlp(cmd)

        if not success and critical:
            logger.error("❌ Error crítico en la descarga.")
            return

        files = extract_files(TEMP_MUSIC_PATH)
        files = album_postprocessor.actualizar_indice_pista(files)

        first: bool = True
        album_name: str = None

        for song in files:
            audio_ext = str(song.suffix).rsplit(".", 1)[-1].lower()
            handler = AudioHandlerFactory().get_handler(audio_ext)

            try:
                comment = handler.extract_comment(str(song))
                if not comment:
                    continue

                raw_metadata = yt_dlp_service.fetch_raw_metadata(comment)

                tags_to_extract = list(vars(Metadata()).keys())
                tags_to_extract.remove("Album")

                metadata_obj = album_postprocessor.extract_metadata(raw_metadata, tags_to_extract)

                if not artist:
                    artist = Transform.sanitize_path_component(metadata_obj.Artist)
                    if artist and ";" in artist:
                        artist = artist.split(";")[0].strip()

                if first:
                    first = False

                    album_postprocessor.actualizar_portada(files, artist)

                    # 🔥 AQUÍ ESTÁ EL CAMBIO IMPORTANTE
                    if playlist_title:
                        album_name = Transform.sanitize_path_component(playlist_title)
                    else:
                        album_name = Transform.sanitize_path_component(
                            handler.getMetadata(song, ["Album"]).Album
                        )

                    # Ajuste de artista existente
                    for directory in MUSIC_ROOT_PATH.iterdir():
                        if directory.is_dir() and directory.name.lower() == metadata_obj.Artist.lower():
                            artist = directory.name
                            break

                audio = handler.open_file(str(song))
                handler.apply_metadata(audio, metadata_obj, tags_to_extract, artist)
                audio.save()

                yt_dlp_service.flush_batch_cache()

            except Exception as e:
                yt_dlp_service.flush_batch_cache()
                logger.error(f"Error procesando archivo {song}: {e}")

        if album_name:
            final_path = MUSIC_ROOT_PATH / artist / album_name
            final_path.mkdir(parents=True, exist_ok=True)

            for song in files:
                destino = final_path / song.name
                if not destino.exists():
                    shutil.move(str(song), str(destino))
                else:
                    logger.info(f"El archivo {destino} ya existe, se omite mover.")
        else:
            logger.error("No se pudo obtener el nombre del album.")