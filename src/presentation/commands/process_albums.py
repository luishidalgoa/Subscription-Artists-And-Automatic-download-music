#app/presentation/commands/process_albums.py
from src.domain.base_command import BaseCommand
from src.infrastructure.service.album_postprocessor import procesar_albumes
from src.infrastructure.config.config import ARTISTS_FILE, ROOT_PATH
from src.application.providers.logger_provider import LoggerProvider
import json

logger = LoggerProvider()

DESCRIPCION = "Procesa todos los albumes o singles descargados de los artistas de artists.json"

class ProcessAlbumsCommand(BaseCommand):
    DESCRIPCION = DESCRIPCION
    ARGUMENTOS = {
        "--artist": {
            "params": {
                "required": False,
                "help": "Nombre del artista a procesar (opcional)"
            }
        }
    }

    def handle(self, parsed_args):
        """
        Procesa los álbumes de artistas, con filtro opcional por nombre.
        """
        artist = getattr(parsed_args, "artist", None)
        if artist:
            # Eliminar comillas simples o dobles al inicio y final
            artist = artist.strip("'\"")


        try:
            with ARTISTS_FILE.open() as f:
                artists = json.load(f)
        except Exception as e:
            logger.error(f"Error al leer artists.json: {e}")
            return

        for artist_data in artists:
            name = artist_data["name"]

            # Si se especifica un artista, solo procesar ese
            if artist and name != artist:
                continue

            output_path = ROOT_PATH / name
            procesar_albumes(output_path, {"filter_by_date": False})