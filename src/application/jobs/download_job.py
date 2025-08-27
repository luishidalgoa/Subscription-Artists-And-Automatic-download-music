from src.domain.scheduler.base_job import BaseJob
from src.domain.scheduler.time_unit import TimeUnit
from src.presentation.controller.download_controller import run_descargas
from src.infrastructure.service.update_service import actualizar_app
from src.infrastructure.config.config import update_now as update_time_now
from src.application.providers.logger_provider import LoggerProvider

logger = LoggerProvider()
class DownloadJob(BaseJob):
    def __init__(self):
        super().__init__(name="DownloadJob", time_unit=TimeUnit.MINUTES, interval=2,id=None)

    def run(self):
        actualizar_app()
        update_time_now()
        run_descargas()
