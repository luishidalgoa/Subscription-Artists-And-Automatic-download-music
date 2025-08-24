# app/controller/download_controller.py
import json
import subprocess
from app.config import ARTISTS_FILE, LAST_RUN_FILE, ROOT_PATH
from app.service.album_postprocessor import procesar_albumes
import os
from app.providers.logger_provider import LoggerProvider
logger = LoggerProvider()
from app.config import now,COOKIES_FILE
from app.service.console_reader_service import run_yt_dlp

def run_descargas():
    try:
        try:
            with ARTISTS_FILE.open() as f:
                artists = json.load(f)
        except Exception as e:
            logger.error(f"Error al leer artists.json: {e}")
            return

        if LAST_RUN_FILE.exists():
            with LAST_RUN_FILE.open() as f:
                last_run = json.load(f)
        else:
            last_run = {}

        for artist in artists:
            name = artist["name"]
            url = artist["channel_url"]
            logger.info(f"▶ Procesando artista: {name}")

            since_time = last_run.get(name, now)
            output_path = ROOT_PATH / name
            output_path.mkdir(parents=True, exist_ok=True)
            output_template = str(output_path / "%(playlist_title)s" / "%(title)s.%(ext)s")

            command = [
                "yt-dlp",
                "--cookies", str(COOKIES_FILE),
                "--quiet",
                "--extract-audio",
                "--audio-format", "mp3",
                "--no-overwrites",
                "--add-metadata",
                "--embed-thumbnail",
                "--sleep-interval", "5",
                "--max-sleep-interval","10",
                "--dateafter", since_time[:10].replace('-', ''),
                "--break-on-reject",
                "-o", output_template,
                url
            ]

            success = run_yt_dlp(command)

            if not success:
                logger.warning(f"⏹ Abortado proceso para {name} por error crítico.")
                return

            logger.info(f"  ↳ Descarga completada para {name}.")
            procesar_albumes(output_path)
            last_run[name] = now

        # guardar marcas de última ejecución
        with LAST_RUN_FILE.open("w") as f:
            json.dump(last_run, f, indent=2)
            f.flush()
            os.fsync(f.fileno())

        logger.info("✅ Proceso completado.")

    except KeyboardInterrupt:
        logger.warning("⏹ Proceso detenido manualmente por el usuario.")
        return
