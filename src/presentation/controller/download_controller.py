# app/controller/download_controller.py
import json
import subprocess
from src.infrastructure.config.config import ARTISTS_FILE, LAST_RUN_FILE, MUSIC_ROOT_PATH
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

def _to_www(url: str) -> str:
    """
    Normaliza dominios de YouTube Music a www.youtube.com.

    yt-dlp no soporta music.youtube.com directamente (redirige internamente), así que
    lo hacemos explícito para poder construir la pestaña /releases del mismo canal.
    """
    return (
        url.replace("https://music.youtube.com", "https://www.youtube.com")
           .replace("http://music.youtube.com", "https://www.youtube.com")
    )


def _build_release_candidates(url: str) -> list[str]:
    """
    URLs candidatas (en orden de preferencia) para listar los lanzamientos de un artista.

    - Para un enlace de canal/artista (incluido YouTube Music) se intenta primero la
      pestaña /releases en www.youtube.com, que agrupa los lanzamientos como playlists
      (un álbum por release). Es el comportamiento ya existente del proyecto.
    - Si ese canal no tiene pestaña /releases (p.ej. canales "- Topic"), se cae a la
      propia URL del canal, que devuelve pistas sueltas → se tratan como un álbum único.
    - Para un enlace directo de playlist/álbum (music.youtube.com/playlist?list=...) se
      usa tal cual → álbum único.
    """
    www = _to_www(url)
    is_playlist_link = "list=" in www
    candidates: list[str] = []

    if not is_playlist_link:
        base = www.split("?")[0].rstrip("/")
        for tab in ("/releases", "/videos", "/featured", "/playlists", "/albums", "/streams"):
            if base.endswith(tab):
                base = base[: -len(tab)]
                break
        candidates.append(base + "/releases")

    if www not in candidates:
        candidates.append(www)

    return candidates


def _flat_dump(url: str) -> dict | None:
    """Devuelve el JSON agregado (yt-dlp --flat-playlist -J) de una URL, o None si falla."""
    cmd = [
        "yt-dlp",
        "--cookies", str(COOKIES_FILE),
        "-J", "--flat-playlist",
        url,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return None


def _clean_album_title(title: str) -> str:
    """Limpia títulos auto-generados de canales (p.ej. 'Uploads from X - Topic')."""
    t = (title or "").strip()
    if t.lower().startswith("uploads from "):
        t = t[len("uploads from "):]
    for suffix in (" - Topic", " – Topic", " - Tema"):
        if t.endswith(suffix):
            t = t[: -len(suffix)]
    return t.strip() or "Desconocido"


def _is_already_downloaded(title: str, subfolders: dict) -> bool:
    """True si ya existe una carpeta para ese título (comparando sanitizado y normalizado)."""
    safe_title = Transform.sanitize_path_component(title)
    normalized_title = Transform.normalize_name(title)
    return (
        safe_title in subfolders
        or normalized_title in {Transform.normalize_name(k) for k in subfolders}
    )


def get_artist_playlists(url: str, artist_root: Path):
    """
    Devuelve los álbumes/lanzamientos NUEVOS de un artista comparando contra el filesystem.

    Soporta:
      - Canales con pestaña /releases (YouTube y YouTube Music) → un álbum por release.
      - Enlaces directos de playlist/álbum (incl. music.youtube.com/playlist?list=...).
      - Canales que solo exponen pistas sueltas (p.ej. canales "- Topic") → álbum único.
    """
    # Carpeta existente real (sanitizada)
    subfolders = {
        Transform.sanitize_path_component(p.name): p
        for p in artist_root.iterdir()
        if p.is_dir()
    }

    for candidate in _build_release_candidates(url):
        data = _flat_dump(candidate)
        if not data:
            continue

        entries = data.get("entries") or []
        if not entries:
            continue

        playlist_entries = [e for e in entries if "playlist" in (e.get("url") or "")]

        # MODO ÁLBUMES: el canal lista sus lanzamientos como playlists (pestaña /releases)
        if playlist_entries:
            playlists = []
            for item in playlist_entries:
                raw_title = item.get("title", f"Playlist_{item.get('id')}")
                if not _is_already_downloaded(raw_title, subfolders):
                    playlists.append({
                        "id": item["id"],
                        "title": raw_title,
                        "url": item["url"],
                    })
            return playlists

        # MODO ÁLBUM ÚNICO: playlist/álbum suelto o canal que solo expone pistas sueltas.
        # La URL completa se baja como un único álbum nombrado con el título del canal/playlist.
        raw_title = _clean_album_title(data.get("title"))
        if _is_already_downloaded(raw_title, subfolders):
            return []
        return [{"id": data.get("id") or raw_title, "title": raw_title, "url": candidate}]

    logger.warning(f"No se obtuvieron entradas de yt-dlp para {url}")
    return []


def run_descargas(new_playlists_download_all: bool = False):
    try:
        artists = artists_load()
        last_run = last_run_load()

        for artist in artists:
            safe_name = Transform.sanitize_path_component(artist["name"])
            url = artist["channel_url"]

            logger.info(f"▶ Procesando artista: {artist['name']}")

            since_time = last_run.get(artist["name"], now)

            output_path = MUSIC_ROOT_PATH / safe_name
            output_path.mkdir(parents=True, exist_ok=True)

            playlists = get_artist_playlists(url, output_path)

            for pl in playlists:
                raw_title = pl["title"]  # 👈 NOMBRE REAL del album
                safe_title = Transform.sanitize_path_component(raw_title)
                logger.info(f"▶ Procesando playlist: {safe_title}")

                playlist_path = output_path / safe_title
                is_new = not playlist_path.exists()

                playlist_path.mkdir(parents=True, exist_ok=True)

                output_template = str(playlist_path / "%(autonumber)02d. %(title)s.%(ext)s")

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

                success, critical = run_yt_dlp(cmd)

                if not success and critical:
                    logger.warning(
                        f"⏹ Abortado en playlist {raw_title} de {artist['name']}"
                    )
                    return

            if playlists:
                logger.info(f"  ↳ Descarga completada para {artist['name']}. Procesando álbumes...")
                procesar_albumes(output_path)
            else:
                logger.warning(f"⚠ No se encontraron playlists nuevas para {artist['name']}")

            last_run[artist["name"]] = now

        with LAST_RUN_FILE.open("w") as f:
            json.dump(last_run, f, indent=2)
            f.flush()
            os.fsync(f.fileno())

        logger.info("✅ Proceso completado.")

    except KeyboardInterrupt:
        logger.error("❌ Descarga interrumpida manualmente por el usuario. Todos los procesos activos se detuvieron.")
