import json
from src.application.providers.logger_provider import LoggerProvider
from src.domain.base_command import BaseCommand
from src.infrastructure.config.config import ARTISTS_FILE


logger = LoggerProvider()

class ListArtistsCommand(BaseCommand):
    DESCRIPCION = "Lista todos los artistas disponibles"

    def handle(self, parsed_args):
        try:
            with ARTISTS_FILE.open() as f:
                artists = json.load(f)
        except Exception as e:
            logger.error("❌ No se pudo leer el archivo 'artists.json'", exc_info=e)
            return

        if not artists:
            logger.warning("⚠️ No hay artistas registrados en la aplicación.")
            return

        logger.info("🎵 Lista de artistas disponibles:")
        for idx, artist in enumerate(artists, start=1):
            logger.info(f"   {idx:02d}. {artist['name']}")
        logger.info(f"Total de artistas: {len(artists)}")