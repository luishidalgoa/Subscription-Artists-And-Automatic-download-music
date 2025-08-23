DESCRIPCION = "Actualiza y ejecuta la programación de ejecución de procesos. pero no ejecuta los procesos en el momento del arranque"
from app.scheduler import start_scheduler
from app.config import  update_now as update_time_now
from app.service.update_service import actualizar_app

def ejecutar():
    actualizar_app()
    update_time_now()
    start_scheduler()
