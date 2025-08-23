# app/commands/run_now.py
DESCRIPCION = "Ejecuta la actualización de la app, descarga el contenido de youtube y mantiene el scheduler activo"

from app.providers.logger_provider import LoggerProvider
from app.service.update_service import actualizar_app
from app.controller.download_controller import run_descargas
from app.scheduler import start_scheduler

logger = LoggerProvider()

def ejecutar():
    logger.info("🔄 Actualizando la aplicación...")
    actualizar_app()

    logger.info("▶ Ejecución de descargas automáticas...")
    run_descargas()
    start_scheduler()
