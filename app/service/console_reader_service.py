# app/service/console.reader.service.py
import subprocess
import logging

logger = logging.getLogger(__name__)

def run_yt_dlp(command: list[str]) -> bool:
    """
    Ejecuta yt-dlp y pasa cada línea por los detectores de errores.
    Devuelve True si no se detectó ningún error crítico,
    False si hubo que abortar.
    """
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,      # 👈 sin esto process.stdout será None
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )


    error_detected = False
    for line in process.stdout:
        line = line.strip()
        logger.info("hola "+line)
        if line:
            logger.debug(f"[yt-dlp] {line}")

        # probar cada detector
        for detector in ERROR_DETECTORS:
            if detector(line):  # si detecta error, abortamos
                error_detected = True
                process.terminate()
                process.wait()
                break

        if error_detected:
            break

    process.wait()

    return not error_detected


def detect_ip_ban(line: str) -> bool:
    patterns = [
        "Sign in to confirm you’re not a bot",
        "Sign in to confirm you're not a bot",
        "Use --cookies-from-browser or --cookies for the authentication"
    ]
    if any(p in line for p in patterns):
        logger.error("🚫 YouTube ha bloqueado temporalmente la IP (captcha / bot check).")
        return True
    return False

ERROR_DETECTORS = [
    detect_ip_ban,
]