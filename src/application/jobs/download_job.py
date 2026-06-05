from src.domain.scheduler.base_job import BaseJob
from src.domain.scheduler.time_unit import TimeUnit
from src.presentation.controller.download_controller import run_descargas
from src.infrastructure.config.config import update_now as update_time_now
from src.application.providers.logger_provider import LoggerProvider

logger = LoggerProvider()
class DownloadJob(BaseJob):
    def __init__(self, new_playlists_download_all: bool = False):
        super().__init__(name="DownloadJob", time_unit=TimeUnit.DAYS, interval=5,id=None)
        self.new_playlists_download_all = new_playlists_download_all

    def run(self):
        # yt-dlp se mantiene fresco vía rebuild de imagen (workflow yt-dlp-watch),
        # no en runtime (el contenedor non-root no puede autoactualizarlo).
        update_time_now()  # refresca config.now para esta ejecución (timestamps/last_run)
        run_descargas(new_playlists_download_all=self.new_playlists_download_all)
