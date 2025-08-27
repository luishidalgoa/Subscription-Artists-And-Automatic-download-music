# app/service/yt_dlp.py
import subprocess
from src.application.providers.logger_provider import LoggerProvider

logger = LoggerProvider()  # usa solo este

def actualizar_app():
    logger.info("🔄 Actualizando la aplicación...")
    _actualizar_yt_dlp()

def _actualizar_yt_dlp():
    try:
        resultado = subprocess.run(
            ["yt-dlp", "-U"],
            check=True,
            capture_output=True,
            text=True
        )

        salida = resultado.stdout.strip() or resultado.stderr.strip()  # por si escribe en stderr
        if "yt-dlp is up to date" in salida.lower():
            logger.info("yt-dlp ya estaba en la última versión. No se ha actualizado.")
        else:
            logger.info(f"yt-dlp actualizado correctamente: {salida}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Error actualizando yt-dlp: {e}")
