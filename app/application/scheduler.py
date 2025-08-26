# app/application/scheduler.py
from app.infrastructure.service.scheduler_service import SchedulerService
from app.application.jobs.download_job import DownloadJob

def download_job():
    """
    Registra un job de descarga de álbumes/novedades en el SchedulerService.

    Flujo:
        1. Instancia un objeto `SchedulerService` que maneja la planificación de jobs.
        2. Crea una instancia de `DownloadJob`, que contiene:
           - `name`: nombre descriptivo del job.
           - `interval`: frecuencia con la que se ejecutará.
           - `time_unit`: unidad de tiempo para la frecuencia (días, horas, etc.).
        3. Llama a `SchedulerService.add_job()` pasando:
           - `name`: obtenido de `download_job.get_name()`.
           - `func`: método `download_job.run` que ejecuta la lógica de la descarga.
           - `every`: intervalo de repetición (`download_job.get_interval()`).
           - `unit`: unidad de tiempo (`download_job.get_time_unit()`).
        4. Retorna la instancia del scheduler para que el que llame pueda decidir
           si desea iniciar el loop `run_forever()` o controlar la ejecución de otra manera.

    Retorna:
        SchedulerService: instancia del scheduler con el job de descarga registrado.
    """
    scheduler = SchedulerService()
    download_job = DownloadJob()
    scheduler.add_job(
        name=download_job.get_name(),
        func=download_job.run,
        every=download_job.get_interval(),
        unit=download_job.get_time_unit()
    )
    return scheduler