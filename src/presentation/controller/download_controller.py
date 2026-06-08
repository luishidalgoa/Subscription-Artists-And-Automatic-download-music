# app/controller/download_controller.py
import json
import subprocess
from src.infrastructure.config.config import ARTISTS_FILE, LAST_RUN_FILE, MUSIC_ROOT_PATH, TEMP_MUSIC_PATH
from src.infrastructure.system.json_loader import artists_load, last_run_load
from src.infrastructure.service.album_postprocessor import procesar_album
import os
import shutil
from src.application.providers.logger_provider import LoggerProvider
from src.utils.Transform import Transform
logger = LoggerProvider()
from src.infrastructure.config.config import COOKIES_FILE
from src.infrastructure.config import config as app_config
from src.infrastructure.service.yt_dlp_service import run_yt_dlp, PROGRESS_PRINT
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
        "--js-runtimes", "node",
        "-J", "--flat-playlist",
        url,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    except subprocess.TimeoutExpired:
        logger.warning(f"yt-dlp tardó demasiado (timeout) al listar {url}")
        return None
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

        raw_title = _clean_album_title(data.get("title"))

        # MODO CANAL TOPIC: el canal (p.ej. "X - Topic") no agrupa en playlists, solo
        # expone pistas sueltas, pero CADA pista trae su campo `album` en los metadatos.
        # Dejamos que yt-dlp reparta la descarga en una carpeta por álbum (%(album)s) en
        # vez de volcar todo en una sola carpeta con el nombre del artista.
        is_playlist_link = "list=" in candidate
        if not is_playlist_link:
            return [{
                "id": data.get("id") or raw_title,
                "title": raw_title,
                "url": candidate,
                "split_by_album": True,
            }]

        # MODO ÁLBUM ÚNICO: enlace directo de playlist/álbum suelto (list=...).
        # Se baja como un único álbum nombrado con el título de la playlist.
        if _is_already_downloaded(raw_title, subfolders):
            return []
        return [{"id": data.get("id") or raw_title, "title": raw_title, "url": candidate}]

    logger.warning(f"No se obtuvieron entradas de yt-dlp para {url}")
    return []


def _save_last_run(last_run: dict) -> None:
    """Persiste last_run.json de forma atómica (escritura + fsync). No relanza errores."""
    try:
        with LAST_RUN_FILE.open("w") as f:
            json.dump(last_run, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
    except Exception as e:
        logger.error(f"No se pudo guardar last_run.json: {e}")


def _existing_album_match_filter(music_artist_dir: Path) -> list:
    """`--match-filter` que EXCLUYE de la descarga los álbumes ya presentes en /music.

    Usa igualdad exacta (`album!=...`) para no excluir por subcadena (evita perder un
    álbum nuevo cuyo nombre contenga al de uno existente). Solo incluye nombres seguros
    para el parser de yt-dlp (sin `&` ni comillas); los demás los atrapa el chequeo
    autoritativo al mover, sin pérdida de datos. Devuelve [] si no hay nada que excluir.
    """
    if not music_artist_dir.exists():
        return []
    safe = [
        p.name for p in music_artist_dir.iterdir()
        if p.is_dir() and all(c not in p.name for c in ('&', '"', '\n'))
    ]
    if not safe:
        return []
    expr = " & ".join(f"album!={n}" for n in safe)
    return ["--match-filter", expr]


def _promote_album(temp_album: Path, music_artist_dir: Path) -> None:
    """Post-procesa un álbum descargado en TEMP y lo MUEVE a /music/<artista> si es nuevo.

    Reusa _is_already_downloaded: si el álbum ya existe en destino, descarta la copia
    temporal (no duplica ni sobrescribe). El post-proceso (P2) se hace en TEMP antes de mover.
    """
    if not temp_album.is_dir():
        return
    if not any(temp_album.iterdir()):
        shutil.rmtree(temp_album, ignore_errors=True)
        return

    music_subfolders = {
        Transform.sanitize_path_component(p.name): p
        for p in music_artist_dir.iterdir() if p.is_dir()
    } if music_artist_dir.exists() else {}

    if _is_already_downloaded(temp_album.name, music_subfolders):
        logger.info(f"⏭ Álbum ya presente en /music, se descarta el temporal: {temp_album.name}")
        shutil.rmtree(temp_album, ignore_errors=True)
        return

    # Post-proceso EN TEMP (todo lo de temp es recién bajado → sin filtro por fecha).
    procesar_album(temp_album, {"filter_by_date": False})

    music_artist_dir.mkdir(parents=True, exist_ok=True)
    dest = music_artist_dir / temp_album.name
    if dest.exists():
        shutil.rmtree(temp_album, ignore_errors=True)
        return
    shutil.move(str(temp_album), str(dest))
    logger.info(f"📦 Álbum movido a /music: {dest.name}")


# Marcadores que yt-dlp deja para la pista EN CURSO (descargando o convirtiendo):
#   .part / .part-Frag  → descarga a medias;  .ytdl → metadatos de reanudación;
#   .temp.<ext>         → conversión de ffmpeg en marcha.
# Su presencia identifica el ÚNICO álbum que se estaba bajando al cortar.
_INPROGRESS_MARKERS = (".part", ".ytdl")
# Restos a borrar de un álbum COMPLETO antes de moverlo (no son audio final).
_JUNK_MARKERS = (".part", ".ytdl", ".webm", ".temp.mp3", ".temp", ".tmp")


def _album_incompleto(album_dir: Path) -> bool:
    """True si el álbum tiene una pista a medias (marcadores de yt-dlp) o está vacío.

    Un álbum cuyos ficheros son solo audio final (.mp3) se considera COMPLETO. Esto
    distingue el álbum que se estaba descargando al interrumpir (lo tiene) de los ya
    terminados (no lo tienen) — sin necesitar saber el número esperado de pistas.
    """
    try:
        names = [p.name.lower() for p in album_dir.iterdir() if p.is_file()]
    except OSError:
        return False
    if not names:
        return True
    return any(
        n.endswith(_INPROGRESS_MARKERS) or ".part-frag" in n or ".temp." in n
        for n in names
    )


def _limpiar_restos(album_dir: Path) -> None:
    """Borra restos que no son audio final (.webm/.part/.temp…) de un álbum completo."""
    try:
        for p in album_dir.iterdir():
            n = p.name.lower()
            if p.is_file() and (n.endswith(_JUNK_MARKERS) or ".part-frag" in n):
                try:
                    p.unlink()
                except OSError:
                    pass
    except OSError:
        pass


def _settle_temp(temp_artist_dir: Path, output_path: Path) -> None:
    """Asienta el temp de un artista de forma segura ante interrupciones.

    Por cada álbum en TEMP: si está a medias (la pista en curso al cortar) se DESCARTA;
    si está completo, se limpian restos y se PROMUEVE a /music. Idempotente: tras la
    primera pasada los completos ya no están y los incompletos se han borrado.
    """
    if not temp_artist_dir.exists():
        return
    for sub in list(obtener_subcarpetas(temp_artist_dir).values()):
        try:
            if _album_incompleto(sub):
                logger.warning(f"🗑 Álbum a medias (descarga interrumpida), se descarta: {sub.name}")
                shutil.rmtree(sub, ignore_errors=True)
            else:
                _limpiar_restos(sub)
                _promote_album(sub, output_path)
        except Exception as e:
            logger.error(f"⚠ Error al asentar el álbum '{sub.name}', se continúa: {e}")


def run_descargas(new_playlists_download_all: bool = False):
    # artists_load/last_run_load degradan a [] / {} ante error → no revientan el bucle.
    artists = artists_load() or []
    last_run = last_run_load() or {}
    # Timestamp FRESCO de esta ejecución (app_config.now se refresca en update_now());
    # leerlo del módulo evita el valor congelado en el import.
    run_ts = app_config.now

    try:
        for artist in artists:
            name = (artist or {}).get("name")
            url = (artist or {}).get("channel_url")
            if not name or not url:
                logger.warning(f"⚠ Artista inválido en artists.json, se omite: {artist!r}")
                continue

            safe_name = Transform.sanitize_path_component(name)
            temp_artist_dir = TEMP_MUSIC_PATH / safe_name  # descargas en curso, aisladas por artista
            try:
                logger.info(f"▶ Procesando artista: {name}")
                since_time = last_run.get(name, run_ts)

                output_path = MUSIC_ROOT_PATH / safe_name
                output_path.mkdir(parents=True, exist_ok=True)

                playlists = get_artist_playlists(url, output_path)

                # Álbumes/playlists EXTRA registrados a mano en artists.json (campo "albums":
                # lista de URLs). Útil para lanzamientos que el feed del canal Topic NO expone
                # (p.ej. SEGA no tiene pestaña /releases ni /playlists). Cada URL se trata como
                # un álbum único y se sincroniza en la misma carpeta del artista.
                for extra_url in (artist.get("albums") or []):
                    try:
                        playlists += get_artist_playlists(extra_url, output_path)
                    except Exception as e:
                        logger.warning(f"⚠ No se pudo procesar el álbum extra {extra_url} de {name}: {e}")

                stop_all = False
                for pl in playlists:
                    raw_title = pl["title"]  # 👈 NOMBRE REAL del album
                    safe_title = Transform.sanitize_path_component(raw_title)
                    extra_args: list = []

                    if pl.get("split_by_album"):
                        # Canal Topic: una carpeta por álbum (yt-dlp reparte con %(album)s).
                        # Sin track_number fiable; el post-proceso reindexa. Se baja a TEMP.
                        logger.info(f"▶ Procesando canal Topic por álbumes: {safe_title}")
                        # En Topic el match-filter (album!=existentes) es AUTORITATIVO sobre
                        # qué álbumes faltan. NO se filtra por fecha: los álbumes ausentes
                        # suelen ser antiguos y --dateafter los bloquearía → con la carpeta
                        # del artista no vacía no se descargaba nada (bug). Sin fecha, yt-dlp
                        # escanea el canal y el match-filter salta los que ya están.
                        usar_dateafter = False
                        # Prefijo %(playlist_index)s: los canales Topic NO traen track_number
                        # y el índice es global del canal, pero las pistas de un álbum vienen
                        # consecutivas → el prefijo (zero-padded) preserva el orden REAL del
                        # álbum en disco. El post-proceso lo reescribe a 1..N por álbum.
                        output_template = str(
                            temp_artist_dir / "%(album|Sin álbum)s" / "%(playlist_index)05d. %(title)s.%(ext)s"
                        )
                        # No bajar álbumes que YA tenemos en /music (ahorra cómputo y espacio).
                        # match-filter (salta y continúa) en lugar de --break-on-reject: los
                        # álbumes existentes están intercalados, no se debe parar al primero.
                        extra_args += _existing_album_match_filter(output_path)
                    else:
                        logger.info(f"▶ Procesando playlist: {safe_title}")
                        # get_artist_playlists ya filtró los álbumes existentes en estos modos.
                        is_new = not (output_path / safe_title).exists()
                        # Releases: incremental por fecha, salvo álbum nuevo en run-now (se baja entero).
                        usar_dateafter = not (is_new and new_playlists_download_all)
                        temp_album = temp_artist_dir / safe_title
                        temp_album.mkdir(parents=True, exist_ok=True)
                        output_template = str(temp_album / "%(autonumber)02d. %(title)s.%(ext)s")
                        extra_args.append("--break-on-reject")

                    cmd = [
                        "yt-dlp",
                        "--cookies", str(COOKIES_FILE),
                        # Sin un runtime JS, yt-dlp cae al cliente web y YouTube lo limita
                        # ("Video unavailable... rate-limited"). node va instalado en la imagen.
                        "--js-runtimes", "node",
                        # Solver EJS oficial: node resuelve el challenge JS (n-sig/signature)
                        # en vez de caer al cliente android, que YouTube marca como bot y
                        # devuelve "Video unavailable" en lotes grandes (p.ej. canales Topic).
                        "--remote-components", "ejs:github",
                        # Silencia los warnings benignos de "Signature/n challenge solving
                        # failed" (el audio se baja igual). Los ERRORES siguen visibles.
                        "--no-warnings",
                        "--quiet",
                        # Progreso: una línea por canción (la pinta run_yt_dlp con \r).
                        "--print", PROGRESS_PRINT,
                        "--extract-audio",
                        "--audio-format", "mp3",
                        "--no-overwrites",
                        "--add-metadata",
                        "--embed-thumbnail",
                        "--sleep-interval", "5",
                        "--max-sleep-interval", "10",
                        *extra_args,
                        "-o", output_template,
                        pl["url"]
                    ]

                    if usar_dateafter:
                        cmd.insert(-1, "--dateafter")
                        cmd.insert(-1, since_time[:10].replace('-', ''))

                    success, critical = run_yt_dlp(cmd)

                    if not success and critical:
                        logger.warning(
                            f"⏹ Abortado en playlist {raw_title} de {name}: error crítico"
                        )
                        stop_all = True
                        break

                # Asienta el temp del artista: promueve a /music los álbumes COMPLETOS y
                # descarta el que se estaba descargando a medias. Se hace al salir del bucle
                # (y se repite en finally como red de seguridad ante Ctrl+C / excepción).
                _settle_temp(temp_artist_dir, output_path)

                if stop_all:
                    # Error crítico (p.ej. bloqueo de IP): detener TODO el run, pero
                    # conservando el progreso de los artistas ya completados. Este
                    # artista NO se marca como completado (se reintentará).
                    _save_last_run(last_run)
                    logger.error("🛑 Run detenido por error crítico (posible bloqueo de IP). Progreso guardado.")
                    return

                if playlists:
                    # El post-proceso ya se hizo álbum a álbum durante la descarga (P2).
                    logger.info(f"  ↳ Descarga y post-proceso completados para {name}.")
                else:
                    logger.warning(f"⚠ No se encontraron playlists nuevas para {name}")

                # Solo se marca completado si llegó hasta aquí sin abortar.
                last_run[name] = run_ts
                _save_last_run(last_run)  # persistencia incremental: no perder progreso

            except Exception as e:
                # Aísla el fallo de un artista para no tumbar el resto del lote
                # (p.ej. RuntimeError de yt-dlp por un exit code no reconocido).
                logger.error(f"❌ Error procesando '{name}', se omite y se continúa: {e}")
                continue
            finally:
                # Red de seguridad: si se interrumpió (Ctrl+C/excepción) antes del
                # asentamiento normal, promueve igualmente los álbumes COMPLETOS y
                # descarta solo el de a-medias (idempotente si ya se asentó arriba).
                _settle_temp(temp_artist_dir, output_path)
                # Elimina el temporal ya vacío (sobrantes, descartados).
                shutil.rmtree(temp_artist_dir, ignore_errors=True)

        _save_last_run(last_run)
        logger.info("✅ Proceso completado.")

    except KeyboardInterrupt:
        logger.error("❌ Descarga interrumpida manualmente por el usuario. Guardando progreso...")
        _save_last_run(last_run)
