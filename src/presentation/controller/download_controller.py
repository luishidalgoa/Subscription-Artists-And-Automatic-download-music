# app/controller/download_controller.py
import json
import subprocess
from src.infrastructure.config.config import ARTISTS_FILE, LAST_RUN_FILE, ROOT_PATH
from src.infrastructure.system.json_loader import artists_load, last_run_load
from src.infrastructure.service.album_postprocessor import procesar_albumes
import os
from src.application.providers.logger_provider import LoggerProvider
from src.utils.Transform import Transform
logger = LoggerProvider()
from src.infrastructure.config.config import now,COOKIES_FILE
from src.infrastructure.service.yt_dlp_service import run_yt_dlp
from src.infrastructure.system.directory_utils import obtener_subcarpetas
from pathlib import Path

def get_artist_playlists(url: str, artist_root: Path):
    """
    Devuelve solo las playlists cuyo título que no coincide con alguna subcarpeta
    existente dentro del root del artista.
    """
    # 1️⃣ Obtener subcarpetas existentes
    subfolders = obtener_subcarpetas(artist_root)  # {nombre_carpeta: Path}

    # 2️⃣ Ejecutar yt-dlp para listar todas las playlists
    cmd = [
        "yt-dlp",
        "--cookies", str(COOKIES_FILE),
        "-j", "--flat-playlist",
        url
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    playlists = []

    for line in result.stdout.splitlines():
        try:
            data = json.loads(line)
            if data.get("url") and "playlist" in data.get("url", ""):
                raw_title = data.get("title", f"Playlist_{data['id']}")
                title = Transform.sanitize_path_component(raw_title)
                # 3️⃣ Filtrar solo playlists que coinciden con subcarpetas
                if title not in subfolders:
                    playlists.append({
                        "id": data["id"],
                        "title": title,
                        "url": data["url"]
                    })
        except json.JSONDecodeError:
            logger.warning(f"No se pudo parsear línea de yt-dlp: {line}")

    return playlists


def run_descargas(new_playlists_download_all: bool = False):
    try:
        artists = artists_load()
        last_run = last_run_load()

        for artist in artists:
            safe_name = Transform.sanitize_path_component(artist["name"])
            url = artist["channel_url"]
            logger.info(f"▶ Procesando artista: {artist['name']}")

            since_time = last_run.get(artist["name"], now)
            output_path = ROOT_PATH / safe_name
            output_path.mkdir(parents=True, exist_ok=True)

            playlists = get_artist_playlists(url, output_path)

            for pl in playlists:
                safe_title = Transform.sanitize_path_component(pl["title"])
                playlist_path = output_path / safe_title
                is_new = not playlist_path.exists()
                playlist_path.mkdir(parents=True, exist_ok=True)
                output_template = str(playlist_path / "%(title)s.%(ext)s")

                # Si la carpeta es nueva y se pasó el flag, no aplicamos --dateafter
                cmd = [
                    "yt-dlp",
                    "--cookies", str(COOKIES_FILE),
                    "--quiet",
                    "--extract-audio",
                    "--audio-format", "mp3",
                    "--no-overwrites",
                    "--add-metadata",
                    "--embed-thumbnail",
                    "--sleep-interval", "5",
                    "--max-sleep-interval", "10",
                    "--break-on-reject",
                    "-o", output_template,
                    pl["url"]
                ]

                if not (is_new and new_playlists_download_all):
                    cmd.insert(-1, "--dateafter")
                    cmd.insert(-1, since_time[:10].replace('-', ''))

                success = run_yt_dlp(cmd)

                if not success:
                    logger.warning(f"⏹ Abortado proceso en playlist {pl['title']} de {artist['name']}.")
                    return

            if playlists:
                logger.info(f"  ↳ Descarga completada para {artist['name']}. Procesando álbumes...")
                procesar_albumes(output_path)
            else:
                logger.warning(f"⚠ No se encontraron playlists para {artist['name']}, saltando.")

            last_run[artist["name"]] = now

        with LAST_RUN_FILE.open("w") as f:
            json.dump(last_run, f, indent=2)
            f.flush()
            os.fsync(f.fileno())

        logger.info("✅ Proceso completado.")

    except KeyboardInterrupt:
        logger.error("❌ Descarga interrumpida manualmente por el usuario. Todos los procesos activos se detuvieron.")
