# app/service/yt_dlp.py
import subprocess
import logging
logger = logging.getLogger(__name__)

import subprocess
import logging

logger = logging.getLogger(__name__)

def actualizar_yt_dlp():
    try:
        resultado = subprocess.run(
            ["yt-dlp", "-U"],
            check=True,
            capture_output=True,
            text=True
        )
        salida = resultado.stdout.strip()
        if "yt-dlp is up to date" in salida.lower():
            logger.info("yt-dlp ya estaba en la última versión. No se ha actualizado.")
        else:
            logger.info(f"yt-dlp actualizado correctamente: {salida}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Error actualizando yt-dlp: {e}")
