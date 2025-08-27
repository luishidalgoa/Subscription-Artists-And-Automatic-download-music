# commands/check_jobs.py
from src.domain.base_command import BaseCommand
from src.infrastructure.repository.job_repository import JobRepository
from src.application.providers.logger_provider import LoggerProvider
from datetime import datetime

logger = LoggerProvider()

DESCRIPCION = "Devuelve una lista de los Jobs programados."

class CheckJobsCommand(BaseCommand):
    DESCRIPCION = DESCRIPCION
    ARGUMENTOS = {}  # Sin parámetros

    def handle(self, parsed_args):
        repo = JobRepository()
        for job in repo.get_jobs():
            interval = (
                (job.next_run_time - datetime.now()).total_seconds() / 60
                if job.next_run_time
                else None
            )
            if interval is not None:
                horas = int(interval // 60)
                minutos = int(interval % 60)
                interval = f"{horas:02}:{minutos:02}"

            log_msg = (
                f"\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🆔 Job ID       : {job.id}\n"
                f"📛 Name         : {job.name}\n"
                f"⏭️ Next Run     : {job.next_run_time}\n"
                f"⏮️ Last Run     : {job.last_run_time}\n"
                f"⏳ Interval     : {interval if interval else 'N/A'}\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            )

            logger.info(log_msg)