# app/presentation/commands/run_now.py
from src.domain.base_command import BaseCommand
from src.application.jobs.download_job import DownloadJob
from src.application.providers.logger_provider import LoggerProvider

logger = LoggerProvider()

DESCRIPCION = "Ejecuta la actualización de la app, descarga el contenido de youtube y mantiene el scheduler activo"

class RunNowCommand(BaseCommand):
    DESCRIPCION = DESCRIPCION
    ARGUMENTOS = {}  # Sin parámetros

    def handle(self, parsed_args):
        logger.info("▶ Ejecución de descargas automáticas...")
        DownloadJob().run()
