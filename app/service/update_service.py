# app/service/yt_dlp.py
import subprocess
import logging
import os
import sys
logger = logging.getLogger(__name__)

import subprocess
import logging
from app.config import REPO_PATH

logger = logging.getLogger(__name__)

def actualizar_app():
    _actualizar_servicio()
    _actualizar_yt_dlp()

def _actualizar_yt_dlp():
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

import subprocess
import logging
import sys

logger = logging.getLogger(__name__)

def _actualizar_servicio():
    """
    Actualiza el repositorio de la aplicación.
    Si hay cambios, termina el proceso para que Docker lo reinicie.
    """
    try:
        # Fetch primero
        subprocess.run(["git", "fetch"], check=True, capture_output=True, text=True)

        # Pull con rebase y autostash
        result = subprocess.run(
            ["git", "pull", "--rebase", "origin", "main"],
            check=True,
            capture_output=True,
            text=True
        )

        output = result.stdout.strip()
        output_lower = output.lower()

        if "up to date" in output_lower:
            logger.info("📂 El repositorio ya estaba actualizado.")
        elif "updating" in output_lower or "fast-forward" in output_lower:
            logger.info("⬆️  El repositorio se actualizó con éxito.")
            logger.info("🔄 Terminando aplicación para reinicio automático...")
            sys.exit(0)
        else:
            logger.info(f"ℹ️ Resultado de la actualización:\n{output}")

    except subprocess.CalledProcessError as e:
        stderr = getattr(e, "stderr", "")
        logger.error(f"❌ Error al actualizar repositorio:\n{stderr}")
