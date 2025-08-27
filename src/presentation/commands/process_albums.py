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
    ARGUMENTOS = {}  # Sin parámetros

    def handle(self, parsed_args):
        try:
            with ARTISTS_FILE.open() as f:
                artists = json.load(f)
        except Exception as e:
            logger.error(f"Error al leer artists.json: {e}")
            return

        for artist in artists:
            name = artist["name"]
            output_path = ROOT_PATH / name
            procesar_albumes(output_path, {"filter_by_date": False})

