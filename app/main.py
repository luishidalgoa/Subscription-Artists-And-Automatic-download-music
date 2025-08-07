# app/main.py
from app.scheduler import start_scheduler
from app.controller.download_controller import run_descargas
from app.utils.logging_config import configurar_logging
import logging
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    configurar_logging()
    
    logger.info("🕒 Servicio activo. Esperando tareas...")
    run_descargas()
    start_scheduler()