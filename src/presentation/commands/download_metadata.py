from src.domain.base_command import BaseCommand
from src.application.providers.logger_provider import LoggerProvider
from src.infrastructure.audio.handler_factory import AudioHandlerFactory
from src.infrastructure.config.config import MUSIC_ROOT_PATH
from src.infrastructure.system.directory_utils import extract_files, obtener_subcarpetas
from src.infrastructure.system.json_loader import artists_load
from src.infrastructure.service import album_postprocessor, yt_dlp_service
from src.infrastructure.utils.progress_bar import ProgressBar
from src.utils.Transform import Transform
from src.domain.Metadata import Metadata

MetadataFields = list(vars(Metadata()).keys())
MetadataFields.remove("Album")

logger = LoggerProvider()


class FetchMetadataCommand(BaseCommand):
    DESCRIPCION = (
        "Extrae metadatos de YouTube usando yt-dlp e inserta campos "
        "seleccionados dentro de los archivos de audio existentes."
    )

    ARGUMENTOS = {
        "--tags": {
            "params": {
                "required": False,
                "help": f"Lista de campos/metadatos a extraer. Campos aceptados: {', '.join(MetadataFields)}",
                "nargs": "*",
                "default": MetadataFields
            }
        },
        "--artists": {
            "params": {
                "required": False,
                "help": "Artistas a extraer: 'All' o un string específico",
                "default": "All"
            }
        },
        "--omit": {
            "params": {
                "required": False,
                "help": "Omite los elementos registrados en la cache",
                "default": True
            }
        }
    }

    def handle(self, parsed_args):
        tags_to_extract = parsed_args.tags or MetadataFields
        artists_param = parsed_args.artists
        omit_cached = parsed_args.omit or True

        if artists_param == "All" or not artists_param:
            artists = artists_load()
            artist_bar = ProgressBar(total=len(artists), prefix="Artistas")

            for artist in artists:
                safe_name = Transform.sanitize_path_component(artist["name"])
                artist_root = MUSIC_ROOT_PATH / safe_name

                subfolders = obtener_subcarpetas(directorio=artist_root)

                # 🔹 Cambio: procesamos álbum por álbum en lugar de todas las canciones juntas
                for album_name, album_path in subfolders.items():
                    album_songs = extract_files(album_path)

                    if not album_songs:
                        continue

                    # Barra de progreso por álbum
                    song_bar = ProgressBar(
                        total=len(album_songs),
                        prefix=f"{artist['name']} - {album_name}"
                    )

                    for song in album_songs:
                        # Progreso de canciones
                        song_bar.update()

                        ext = str(song).rsplit(".", 1)[-1].lower()
                        handler = AudioHandlerFactory.get_handler(ext)

                        if not handler:
                            logger.warning(f"Formato no soportado: {song}")
                            continue

                        try:
                            comment = handler.extract_comment(str(song))
                            if not comment:
                                logger.warning(f"No hay URL de YouTube en el archivo: {song}")
                                continue

                            if omit_cached and yt_dlp_service.is_url_in_cache(comment):
                                continue

                            raw_metadata = yt_dlp_service.fetch_raw_metadata(comment)
                            metadata_obj = album_postprocessor.extract_metadata(
                                raw_metadata,
                                tags_to_extract
                            )

                            audio = handler.open_file(str(song))
                            handler.apply_metadata(
                                audio,
                                metadata_obj,
                                tags_to_extract,
                                artist=artist["name"]
                            )
                            audio.save()

                        except Exception as e:
                            yt_dlp_service.flush_batch_cache()
                            logger.error(f"Error procesando archivo {song}: {e}")

                        yt_dlp_service.flush_batch_cache()

                    # 🔹 Cambio: actualizamos la portada una sola vez por álbum
                    album_postprocessor.actualizar_portada(
                        album_songs,
                        artist["name"]
                    )

                # Al terminar el artista → progreso de artistas
                artist_bar.update()

        else:
            logger.info(f"Procesando solo el artista especificado: {artists_param}")
            logger.error("Funcionalidad para artista específico no implementada aún.")
            # Aquí iría la lógica para un artista específico
