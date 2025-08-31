# commands/check_jobs.py
from src.domain.base_command import BaseCommand
from src.infrastructure.repository.job_repository import JobRepository
from src.application.providers.logger_provider import LoggerProvider
from datetime import datetime

from src.utils.Transform import Transform

logger = LoggerProvider()

DESCRIPCION = "Devuelve una lista de los Jobs programados."

class CheckJobsCommand(BaseCommand):
    DESCRIPCION = DESCRIPCION
    ARGUMENTOS = {}  # Sin parámetros

    def handle(self, parsed_args):
        repo = JobRepository()
        for job in repo.get_jobs():
            if job.next_run_time:
                interval_seconds = (job.next_run_time - datetime.now()).total_seconds()
                interval_str = Transform.seconds_to_ddhhmmss(interval_seconds)
            else:
                interval_str = "N/A"

            log_msg = (
                f"\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🆔 Job ID       : {job.id}\n"
                f"📛 Name         : {job.name}\n"
                f"⏭️ Next Run     : {job.next_run_time}\n"
                f"⏮️ Last Run     : {job.last_run_time}\n"
                f"⏳ Interval     : {interval_str}\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            )

            logger.info(log_msg)