#app/presentation/commands/boot.py
from app.domain.base_command import BaseCommand
from app.infrastructure.service.scheduler_service import SchedulerService
from app.application.jobs.download_job import DownloadJob
from datetime import datetime

DESCRIPCION = "Actualiza y ejecuta la programación de ejecución de procesos. pero no ejecuta los procesos en el momento del arranque"

class BootCommand(BaseCommand):
    DESCRIPCION = DESCRIPCION
    ARGUMENTOS = {}  # Sin parámetros

    def handle(self, parsed_args):
        scheduler = SchedulerService()
        download_job_instance = DownloadJob()
        existing_job = scheduler.get_job_by_name(download_job_instance.get_name())

        if existing_job:
            now = datetime.now()
            if existing_job.next_run_time and existing_job.next_run_time > now:
                delta_days = (existing_job.next_run_time - now).days
                scheduler.add_job(download_job_instance, first_delay=delta_days)
            else:
                scheduler.add_job(download_job_instance)
        else:
            scheduler.add_job(download_job_instance)

        scheduler.run_forever()
