from app.domain.scheduler.base_job import BaseJob
from app.domain.scheduler.time_unit import TimeUnit
from app.presentation.controller.download_controller import run_descargas
from app.infrastructure.service.update_service import actualizar_app
from app.config import update_now as update_time_now

class DownloadJob(BaseJob):
    def __init__(self):
        super().__init__(name="DownloadJob", time_unit=TimeUnit.DAYS, interval=5)

    def run(self):
        actualizar_app()
        update_time_now()
        run_descargas()
