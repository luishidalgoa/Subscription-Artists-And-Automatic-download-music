# app/presentation/commands/run_now.py
from src.domain.base_command import BaseCommand
from src.application.jobs.download_job import DownloadJob
from src.application.providers.logger_provider import LoggerProvider

logger = LoggerProvider()

DESCRIPCION = "Actualiza yt-dlp y descarga los álbumes que aún no estén en la carpeta de cada artista."

class RunNowCommand(BaseCommand):
    DESCRIPCION = DESCRIPCION
    ARGUMENTOS = {}

    def handle(self, parsed_args):
        logger.info("▶ Ejecución de descargas automáticas...")
        # Los álbumes nuevos (ausentes en la carpeta del artista) se descargan completos;
        # los ya existentes se actualizan de forma incremental por fecha.
        DownloadJob(new_playlists_download_all=True).run()
