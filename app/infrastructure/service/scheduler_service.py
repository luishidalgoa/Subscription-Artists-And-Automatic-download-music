# app/infrastructure/service/scheduler_service.py
import schedule
import time
import uuid
from datetime import datetime
from app.infrastructure.repository.job_repository import JobRepository
from app.domain.Job import Job
from app.domain.scheduler.base_job import BaseJob
from datetime import timedelta


class SchedulerService:
    def __init__(self):
        self.repo = JobRepository()

    def add_job(self, job: BaseJob, first_delay: int | None = None):
        """
        Registra un job en el scheduler.

        Parámetros:
            job (BaseJob): instancia de la clase de job a ejecutar.
            first_delay (int, opcional): intervalo para la **primera ejecución**.
                                        Se ignora para ejecuciones futuras.

        Flujo:
            1. Si `first_delay` existe, se programa la primera ejecución con ese valor.
            2. Luego se sigue usando `job.get_interval()` y `job.get_time_unit()` para las ejecuciones posteriores.
            3. Inserta/actualiza el estado en el repositorio con `next_run_time`.
        """
        job_id = str(uuid.uuid4())

        # Primera ejecución con delay especial
        if first_delay is not None:
            first_job = schedule.every(first_delay, job.get_time_unit()).do(
                self._wrap_job_once, job_id, job
            )
        else:
            first_job = schedule.every(job.get_interval(), job.get_time_unit()).do(
                self._wrap_job, job_id, job
            )

        self.repo.upsert_job(
            Job(id=job_id, name=job.get_name(), next_run_time=first_job.next_run, last_run_time=None)
        )
        return job_id

    def _wrap_job_once(self, job_id, job: BaseJob):
        """Ejecuta la primera vez con delay especial y luego programa el job normal."""
        job.run()
        schedule.every(job.get_interval(), job.get_time_unit()).do(
            self._wrap_job, job_id, job
        )
        # Actualizamos en repositorio la primera ejecución
        self.repo.upsert_job(
            Job(
                id=job_id,
                name=job.get_name(),
                next_run_time=datetime.now() + timedelta(**{job.get_time_unit().name.lower(): job.get_interval()}),
                last_run_time=datetime.now()
            )
        )

    def run_forever(self):
        """
        Inicia el bucle infinito del scheduler.

        Flujo:
            - Itera continuamente comprobando si hay jobs pendientes de ejecución
              mediante `schedule.run_pending()`.
            - Realiza una pausa de 1 segundo entre iteraciones para evitar uso excesivo de CPU.
        
        Nota:
            Este método bloquea el hilo principal; en producción 
            suele ejecutarse en un thread o proceso dedicado.
        """
        while True:
            schedule.run_pending()
            time.sleep(1)

    def get_job_by_name(self, name: str):
        """
        Busca un job registrado en el scheduler por su nombre.

        Parámetros:
            name (str): Nombre del job a buscar.

        Retorna:
            Job: Objeto Job correspondiente al nombre buscado, o None si no se encuentra.
        """
        return self.repo.get_job_by_name(name)


    def cancel_job(self, job: Job):
        """
        Cancela un job programado y lo elimina del repositorio.
        """
        if job:
            schedule.cancel_job(job)
            self.repo.remove_job(job.id)

    def already_exist_job(name: str) -> bool:
        """
        Verifica si un job con el nombre dado ya existe en el scheduler.

        Parámetros:
            name (str): Nombre del job a buscar.

        Retorna:
            bool: True si el job existe, False en caso contrario.
        """
        scheduler = SchedulerService()
        job = scheduler.get_job_by_name(name)
        return job is not None