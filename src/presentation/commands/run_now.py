# app/presentation/commands/run_now.py
from src.domain.base_command import BaseCommand
from src.application.jobs.download_job import DownloadJob
from src.application.providers.logger_provider import LoggerProvider

logger = LoggerProvider()

DESCRIPCION = "Ejecuta la actualización de la app, descarga el contenido de youtube y mantiene el scheduler activo"

class RunNowCommand(BaseCommand):
    DESCRIPCION = DESCRIPCION
    ARGUMENTOS = {
        "--ignore-date-new": {
            "help": "Si se crea una carpeta nueva para una playlist, descarga todo su contenido ignorando la fecha.",
            "action": "store_true",
            "default": True,
            "required": True,
        }
    }

    def handle(self, parsed_args):
        logger.info("▶ Ejecución de descargas automáticas...")
        new_playlists_download_all = getattr(parsed_args, "new_playlists_download_all", True)
        DownloadJob(new_playlists_download_all=new_playlists_download_all).run()
