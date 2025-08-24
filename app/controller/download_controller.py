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

def get_artist_playlists(url: str):
    """
    Devuelve todas las playlists de un artista a partir de su URL de canal/releases.
    """
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
            if data.get("_type") == "playlist":
                playlists.append({
                    "id": data["id"],
                    "title": data["title"],
                    "url": f"https://music.youtube.com/playlist?list={data['id']}"
                })
        except json.JSONDecodeError:
            logger.warning(f"No se pudo parsear línea de yt-dlp: {line}")
    return playlists


def run_descargas():
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

        # 1. obtener todas las playlists del artista
        playlists = get_artist_playlists(url)
        if not playlists:
            logger.warning(f"⚠ No se encontraron playlists para {name}, saltando.")
            continue

        # 2. recorrer playlists y descargarlas
        for pl in playlists:
            logger.info(f"  🎶 Descargando playlist: {pl['title']}")
            output_template = str(output_path / pl["title"] / "%(title)s.%(ext)s")

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
                "--retries", "3",
                "--dateafter", since_time[:10].replace('-', ''),
                "--break-on-reject",
                "-o", output_template,
                pl["url"]
            ]

            success = run_yt_dlp(cmd)

            if not success:
                logger.warning(f"⏹ Abortado proceso en playlist {pl['title']} de {name}.")
                return  # aborta todo el proceso del script

        # 3. procesar álbumes del artista al terminar todas sus playlists
        logger.info(f"  ↳ Descarga completada para {name}. Procesando álbumes...")
        procesar_albumes(output_path)
        last_run[name] = now

    # guardar marcas de última ejecución
    with LAST_RUN_FILE.open("w") as f:
        json.dump(last_run, f, indent=2)
        f.flush()
        os.fsync(f.fileno())

    logger.info("✅ Proceso completado.")