# commands/check_jobs.py
from app.domain.base_command import BaseCommand
from app.infrastructure.repository.job_repository import JobRepository
from app.application.providers.logger_provider import LoggerProvider

logger = LoggerProvider()

DESCRIPCION = "Devuelve una lista de los Jobs programados."

class CheckJobsCommand(BaseCommand):
    DESCRIPCION = DESCRIPCION
    ARGUMENTOS = {}  # Sin parámetros

    def handle(self, parsed_args):
        repo = JobRepository()
        for job in repo.get_jobs():
            logger.info(f"Job ID: {job.id},\n Name: {job.name},\n Next Run: {job.next_run_time},\n Last Run: {job.last_run_time}")
