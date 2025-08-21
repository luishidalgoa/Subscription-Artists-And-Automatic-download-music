# app/main.py
import argparse
import logging
from app.scheduler import start_scheduler, reset_scheduler
from app.controller.download_controller import run_descargas
from app.utils.logging_config import configurar_logging
from app.service.update_service import actualizar_yt_dlp

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    configurar_logging()

    parser = argparse.ArgumentParser()
    parser.add_argument("--run-now", action="store_true", help="Ejecuta descargas inmediatamente y reinicia scheduler")
    args = parser.parse_args()

    logger.info("🔄 Actualizando yt-dlp...")
    actualizar_yt_dlp()

    if args.run_now:
        logger.info("▶ Ejecución manual solicitada")
        run_descargas()
        reset_scheduler()  # 👈 aquí pospones el scheduler N días
    else:
        logger.info("🕒 Servicio activo. Esperando tareas...")
        run_descargas()
        start_scheduler()
