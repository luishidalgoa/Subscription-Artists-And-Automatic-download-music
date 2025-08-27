# app/infrastructure/service/scheduler_service.py
import schedule
import time
import uuid
from datetime import datetime, timedelta
from src.application.providers.logger_provider import LoggerProvider
from src.infrastructure.repository.job_repository import JobRepository
from src.domain.Job import Job
from src.domain.scheduler.base_job import BaseJob
from src.domain.scheduler.time_unit import TimeUnit

logger =LoggerProvider()

class SchedulerService:
    def __init__(self):
        self.repo = JobRepository()

    def add_job(self, job: BaseJob, resume_interval: int | None = None):
        """
        Registra un job en el scheduler.
        """
        if(job.id is None):
            job_id = str(uuid.uuid4())
        else:
            job_id = job.id

        # Mapeo del enum a métodos de schedule
        unit_method_map = {
            TimeUnit.SECONDS: "seconds",
            TimeUnit.MINUTES: "minutes",
            TimeUnit.HOURS: "hours",
            TimeUnit.DAYS: "days"
        }
        #todo: aqui esta el problema por el que al reanudar el job no se respeta el intervalo original tras su segunda ejecución
        def schedule_job(interval: int, job_func) -> schedule.Job:
            """Programa un job en el scheduler."""
            method_name = unit_method_map[job.get_time_unit()]
            job: schedule.Job = getattr(schedule.every(interval), method_name).do(job_func, job_id, job)
            job.tag(job_id)
            return job

        # Primera ejecución con delay especial
        if resume_interval is not None:
            logger.info(f"Job reanudado, tiempo restante:{resume_interval}")
            first_job = schedule_job(resume_interval, self._wrap_resume_job)
            return job
        else:
            logger.info(f"Nuevo job programado, tiempo restante:{job.get_interval()}")
            first_job = schedule_job(job.get_interval(), self._wrap_job)

        self.repo.upsert_job(
            Job(id=job_id, name=job.get_name(), next_run_time=first_job.next_run, last_run_time=None)
        )
        return job_id

    def _wrap_resume_job(self, job_id, job: BaseJob):
        """Reanuda el job con el intervalo restante."""
        job.run()
        # La ejecución normal seguirá automáticamente con schedule, no reprogramar manualmente
        self.repo.upsert_job(
            Job(
                id=job_id,
                name=job.get_name(),
                next_run_time=datetime.now() + timedelta(**{job.get_time_unit().name.lower(): job.get_interval()}),
                last_run_time=datetime.now()
            )
        )

    def _wrap_job(self, job_id, job: BaseJob):
        """Ejecuta el job y actualiza la próxima ejecución en el repositorio."""
        logger.info(f"Ejecutando job de manera regular, id: {job.id}")
        job.run()

        # Actualizamos el job en el repositorio
        self.repo.upsert_job(
            Job(
                id=job_id,
                name=job.get_name(),
                next_run_time=datetime.now() + timedelta(**{job.get_time_unit().name.lower(): job.get_interval()}),
                last_run_time=datetime.now()
            )
        )


    def run_forever(self):
        """Inicia el bucle infinito del scheduler."""
        while True:
            schedule.run_pending()
            time.sleep(1)

    def get_job_by_name(self, name: str):
        return self.repo.get_job_by_name(name)

    def get_job_by_id(self, job_id: str):
        return self.repo.get_job_by_id(job_id)

    def cancel_job(self, job: Job):
        if job:
            schedule.cancel_job(job)
            self.repo.remove_job(job.id)

    @staticmethod
    def already_exist_job(name: str) -> bool:
        scheduler = SchedulerService()
        job = scheduler.get_job_by_name(name)
        return job is not None
