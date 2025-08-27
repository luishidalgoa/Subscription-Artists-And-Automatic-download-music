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
    ARGUMENTOS = {}

    def handle(self, parsed_args):
        scheduler = SchedulerService()
        download_job_instance = DownloadJob()
        existing_job = scheduler.get_job_by_name(download_job_instance.get_name())

        if existing_job:
            download_job_instance.id = existing_job.id
            now = datetime.now()
            if existing_job.next_run_time and existing_job.next_run_time > now:
                # ✅ calcular diferencia en segundos reales
                delta_seconds = int((existing_job.next_run_time - now).total_seconds())
                scheduler.add_job(download_job_instance, resume_interval_seconds=delta_seconds)
            else:
                scheduler.cancel_job(existing_job)
                scheduler.add_job(download_job_instance)
        else:
            scheduler.add_job(download_job_instance)

        scheduler.run_forever()
