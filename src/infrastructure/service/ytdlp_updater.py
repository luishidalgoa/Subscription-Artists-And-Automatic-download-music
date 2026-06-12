# app/infrastructure/service/ytdlp_updater.py
"""
Actualiza yt-dlp en tiempo de ejecución, antes de cada descarga.

Contexto: el contenedor corre como usuario NO-root (USER 1000), así que NO puede
tocar el yt-dlp instalado a nivel de sistema (/usr/local) ni usar `yt-dlp -U`. La única
vía válida es `pip install --user --upgrade yt-dlp`, que escribe en ~/.local (propiedad
del uid 1000). Por eso el Dockerfile fija HOME=/home/luish: así --user tiene un destino
escribible y determinista.

Esto COMPLEMENTA al workflow `yt-dlp-watch.yml` (que reconstruye la imagen cuando sale
una release nueva): si ese cron se para —GitHub deshabilita los `schedule` tras 60 días
sin actividad—, esta comprobación en runtime mantiene yt-dlp fresco igualmente.

Filosofía: NUNCA debe tumbar la ejecución. Si no hay red o pip falla, se avisa y se sigue
con la versión que ya esté instalada.
"""
import importlib
import os
import site
import subprocess
import sys

from src.application.providers.logger_provider import LoggerProvider

logger = LoggerProvider()


def _is_enabled() -> bool:
    """Permite desactivar la comprobación con YTDLP_AUTO_UPDATE=0/false/no/off."""
    val = os.getenv("YTDLP_AUTO_UPDATE", "1").strip().lower()
    return val not in ("0", "false", "no", "off")


def _installed_version() -> str:
    """Versión de yt-dlp visible para ESTE proceso (lee el dist-info del disco)."""
    try:
        from importlib.metadata import version
        return version("yt-dlp")
    except Exception:
        try:
            from yt_dlp.version import __version__
            return __version__
        except Exception:
            return "desconocida"


def _activate_user_site() -> None:
    """
    Hace visible la copia recién instalada en ~/.local para ESTE proceso:
      - PATH: antepone ~/.local/bin para que el subprocess `yt-dlp` use el binario nuevo.
      - sys.path: inserta el user site-packages para que `import yt_dlp` resuelva al nuevo.
    Sin esto, el proceso seguiría usando el yt-dlp de /usr/local hasta el siguiente arranque.
    """
    try:
        user_base = site.getuserbase()
        user_site = site.getusersitepackages()
    except Exception:
        return

    user_bin = os.path.join(user_base, "bin")
    path_parts = os.environ.get("PATH", "").split(os.pathsep)
    if os.path.isdir(user_bin) and user_bin not in path_parts:
        os.environ["PATH"] = user_bin + os.pathsep + os.environ.get("PATH", "")

    if os.path.isdir(user_site) and user_site not in sys.path:
        sys.path.insert(0, user_site)
        importlib.invalidate_caches()


def ensure_latest_ytdlp(timeout: int = 180) -> None:
    """Comprueba e instala la última yt-dlp (a nivel de usuario). Idempotente y no-fatal."""
    if not _is_enabled():
        logger.info("⏭ Comprobación de yt-dlp desactivada (YTDLP_AUTO_UPDATE).")
        return

    before = _installed_version()
    logger.info(f"⏫ Comprobando actualización de yt-dlp (instalada: {before})...")

    cmd = [
        sys.executable, "-m", "pip", "install",
        "--user", "--upgrade", "--no-input", "--disable-pip-version-check",
        "yt-dlp",
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        logger.warning(f"⚠️ La comprobación de yt-dlp superó {timeout}s; se sigue con {before}.")
        return
    except Exception as e:
        logger.warning(f"⚠️ No se pudo comprobar la actualización de yt-dlp ({e}); se sigue con {before}.")
        return

    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "").strip().splitlines()
        detail = detail[-1] if detail else "sin detalle"
        logger.warning(f"⚠️ No se pudo actualizar yt-dlp (¿sin red?); se usa {before}. Detalle: {detail}")
        return

    _activate_user_site()

    after = _installed_version()
    if before == after:
        logger.info(f"✓ yt-dlp ya estaba al día ({after}).")
    else:
        logger.info(f"✓ yt-dlp actualizado: {before} → {after}.")
