# app/service/console.reader.service.py
import subprocess
from app.application.providers.logger_provider import LoggerProvider

logger= LoggerProvider()

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
        if line:
            logger.debug(f"[yt-dlp] {line}")

            # Detectar descarga completada
            if line.startswith("[ExtractAudio] Destination:") or "has already been downloaded" in line:
                # extraer el nombre del archivo
                title = line.split("Destination:")[-1].strip() if "Destination:" in line else line
                logger.info(f"🎵 Descargado: {title}")

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