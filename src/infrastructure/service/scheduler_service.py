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
from src.utils.time_formatter import convert_timeUnit_to_seconds

logger =LoggerProvider()

class SchedulerService:
    def __init__(self):
        self.repo = JobRepository()

    def add_job(self, job: BaseJob, resume_interval_seconds: int | None = None)-> str:
        """
        Registra un job en el scheduler.

        - Si `resume_interval_seconds` es None, programa el job con su intervalo original
        y lo guarda en la BBDD.
        - Si `resume_interval_seconds` tiene valor, se considera una reanudación:
            * Programa una única ejecución usando ese intervalo temporal.
            * Marca el job como `is_resumed = True` en la BBDD.
            * En la primera ejecución, `_wrap_resume_job` se encargará de
            reprogramarlo con el intervalo original.

        Args:
            job (BaseJob): Job a programar.
            resume_interval_seconds (int | None): Intervalo temporal de reanudación en **segundos**.

        Returns:
            str: ID del job programado.
        """
        if(job.id is None):
            job_id = str(uuid.uuid4())
        else:
            job_id = job.id

        def schedule_job(interval_seconds: int, job_func) -> schedule.Job:
            """Programa un job en el scheduler."""
            scheduled_job: schedule.Job = schedule.every(interval_seconds).seconds.do(job_func, job_id, job)
            scheduled_job.tag(job_id)
            return scheduled_job


        # Si es una reanudación
        if resume_interval_seconds is not None:
            db_job = self.repo.get_job_by_id(job_id)
            if db_job and not db_job.is_resumed:
                db_job.is_resumed = True
                self.repo.upsert_job(db_job)
            first_job = schedule_job(resume_interval_seconds, self._wrap_resume_job)
            return job_id
        else:
            first_job = schedule_job(convert_timeUnit_to_seconds(job.get_interval(), job.get_time_unit()), self._wrap_job)
            self.repo.upsert_job(
                Job(
                    id=job_id,
                    name=job.get_name(),
                    next_run_time=first_job.next_run,
                    last_run_time=None,
                    is_resumed=False  # <--- esta línea es la que agregué
                )
            )

        return job_id
    
    def _wrap_resume_job(self, job_id, job: BaseJob):
        """
        Envuelve la ejecución de un job reanudado.

        - Ejecuta el job una vez (reanudación).
        - Si el job estaba marcado como `is_resumed = True`:
            * Lo reprograma con su intervalo original.
            * Actualiza `next_run_time` y `last_run_time`.
            * Marca `is_resumed = False` en la BBDD.
        - Si no estaba marcado como reanudado (caso defensivo), lo trata como ejecución normal.

        Args:
            job_id (str): Identificador del job.
            job (BaseJob): Instancia del job a ejecutar.
        """
        job.run()

        db_job = self.repo.get_job_by_id(job_id)

        #si es true significa que debemos normalizarlo a false
        if db_job and db_job.is_resumed:

            # Cancelamos el viejo job
            schedule.clear(job_id)

            # Reprogramamos con el intervalo original
            new_job = schedule.every(convert_timeUnit_to_seconds(job.get_interval(), job.get_time_unit())).seconds.do(self._wrap_job, job_id, job)
            new_job.tag(job_id)
            
            db_job.is_resumed = False
            db_job.next_run_time = new_job.next_run
            db_job.last_run_time = datetime.now()

            # Marcamos en la BBDD que ya no está en modo "resumed"
            self.repo.upsert_job(db_job)
        else:
            # Caso defensivo: ya está en ejecución normal
            self._wrap_job(job_id, job)


    def _wrap_job(self, job_id, job: BaseJob):
        """Ejecuta el job y actualiza la próxima ejecución en el repositorio."""
        job.run()

        # Actualizamos el job en el repositorio
        self.repo.upsert_job(
            Job(
                id=job_id,
                name=job.get_name(),
                next_run_time=datetime.now() + timedelta(**{job.get_time_unit().name.lower(): job.get_interval()}),
                last_run_time=datetime.now(),
                is_resumed=False
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
