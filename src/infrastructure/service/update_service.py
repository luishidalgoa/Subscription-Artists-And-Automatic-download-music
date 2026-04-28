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
            capture_output=True,
            text=True
        )

        salida = (resultado.stdout.strip() or resultado.stderr.strip())

        if resultado.returncode == 0:
            if "yt-dlp is up to date" in salida.lower():
                logger.info("yt-dlp ya estaba en la última versión. No se ha actualizado.")
            else:
                logger.info(f"yt-dlp actualizado correctamente: {salida}")
        elif resultado.returncode == 100:
            # En algunos entornos (p.ej. contenedores o instalaciones no autoactualizables)
            # yt-dlp devuelve 100 aunque pueda seguir funcionando con la versión actual.
            logger.warning("No se pudo autoactualizar yt-dlp (código 100). Se continúa con la versión instalada.")
            if salida:
                logger.warning(f"Detalle actualización yt-dlp: {salida}")
        else:
            logger.error(f"Error actualizando yt-dlp (código {resultado.returncode}): {salida}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Error actualizando yt-dlp: {e}")
