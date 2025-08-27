#app/presentation/commands/boot.py
from src.domain.base_command import BaseCommand
from src.infrastructure.service.scheduler_service import SchedulerService
from src.application.jobs.download_job import DownloadJob
from datetime import datetime
from src.application.providers.logger_provider import LoggerProvider

logger = LoggerProvider()

DESCRIPCION = "Actualiza y ejecuta la programación de ejecución de procesos. pero no ejecuta los procesos en el momento del arranque"

class BootCommand(BaseCommand):
    DESCRIPCION = DESCRIPCION
    ARGUMENTOS = {}  # Sin parámetros

    def handle(self, parsed_args):
        scheduler = SchedulerService()
        download_job_instance = DownloadJob()
        existing_job = scheduler.get_job_by_name(download_job_instance.get_name())
        if existing_job:
            download_job_instance.id = existing_job.id
            now = datetime.now()
            if existing_job.next_run_time and existing_job.next_run_time > now:
                delta_days = (existing_job.next_run_time - now).seconds // 60
                scheduler.add_job(download_job_instance, resume_interval=delta_days)
            else:
                scheduler.cancel_job(existing_job)
                scheduler.add_job(download_job_instance)
        else:
            scheduler.add_job(download_job_instance)

        scheduler.run_forever()
