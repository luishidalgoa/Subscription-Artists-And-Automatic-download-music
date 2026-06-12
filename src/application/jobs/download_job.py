from src.domain.scheduler.base_job import BaseJob
from src.domain.scheduler.time_unit import TimeUnit
from src.presentation.controller.download_controller import run_descargas
from src.infrastructure.config.config import update_now as update_time_now
from src.infrastructure.service.ytdlp_updater import ensure_latest_ytdlp
from src.application.providers.logger_provider import LoggerProvider

logger = LoggerProvider()
class DownloadJob(BaseJob):
    def __init__(self, new_playlists_download_all: bool = False):
        super().__init__(name="DownloadJob", time_unit=TimeUnit.DAYS, interval=5,id=None)
        self.new_playlists_download_all = new_playlists_download_all

    def run(self):
        # Antes de cada tanda aseguramos la última yt-dlp. Cubre TODOS los caminos:
        # `run-now` manual y el scheduler (modo boot). Es no-fatal: si no hay red o pip
        # falla, se sigue con la versión instalada. Complementa al rebuild de imagen del
        # workflow yt-dlp-watch para los meses en que ese cron esté parado.
        ensure_latest_ytdlp()
        update_time_now()  # refresca config.now para esta ejecución (timestamps/last_run)
        run_descargas(new_playlists_download_all=self.new_playlists_download_all)
