# app/main.py
from app.scheduler import start_scheduler
from app.controller.download_controller import run_descargas
from app.utils.logging_config import configurar_logging
import logging
logger = logging.getLogger(__name__)
from app.service.yt_dlp import actualizar_yt_dlp

if __name__ == "__main__":
    configurar_logging()
    #ACTUALIZAR YT-DLP
    logger.info("🔄 Actualizando yt-dlp...")
    actualizar_yt_dlp()
    
    logger.info("🕒 Servicio activo. Esperando tareas...")
    run_descargas()
    start_scheduler()