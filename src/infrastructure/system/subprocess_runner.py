import subprocess
from typing import Callable, List, Tuple, Optional

from src.application.providers.logger_provider import LoggerProvider

logger = LoggerProvider()

def run_subprocess_with_detectors(
    command: List[str],
    detectors: List[Callable[[str, Optional[int]], bool]],
    line_callback: Optional[Callable[[str], None]] = None,
) -> Tuple[str, Tuple[bool, bool], Optional[str], int]:
    """
    Ejecuta un comando en subprocess y lee línea por línea en streaming.

    Args:
        command: lista de argumentos del comando.
        detectors: lista de funciones detectoras que reciben cada línea y opcionalmente el returncode.

    Returns:
        (output, success, detected_error, returncode)
          - output: salida completa del proceso (stdout+stderr).
          - Tuple (success, critical):
                - success: True si no se detectó ningún error crítico.
                - critical: True si el error detectado es crítico y detuvo el proceso.
          - detected_error: la línea que disparó el detector (si aplica).
          - returncode: código de salida del proceso
    """
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    output_lines = []
    detected_error = None
    success = True
    critical = False

    # Leer líneas en streaming
    for line in process.stdout:
        line = line.strip()
        if line:
            if line_callback:
                try:
                    line_callback(line)
                except Exception:
                    pass  # el render nunca debe tumbar la descarga
            output_lines.append(line)
            for detector in detectors:
                detected, is_critical = detector(line, None)
                if detected:
                    detected_error = line
                    if is_critical:
                        success = False
                        critical = True
                        process.terminate()
                        process.wait()
                        break
            if critical:
                break

    process.wait()
    returncode = process.returncode
    full_output = "\n".join(output_lines)

    # Detectores que dependen del returncode
    if success and not critical:
        for detector in detectors:
            detected, is_critical = detector(full_output, returncode)
            if detected:
                detected_error = full_output
                if is_critical:
                    success = False
                    critical = True
                else:
                    success = False
                break

    # returncode != 0 sin detector crítico = FALLO PARCIAL, no fatal: en un lote grande
    # (canales Topic con cientos de pistas) es normal que alguna pista falle (fuente
    # corrupta → ffmpeg "Invalid data", vídeo retirado, etc.) y yt-dlp salga con código 1
    # aunque haya bajado bien el resto. Se marca success=False (NO crítico) pero NO se
    # lanza excepción: así el caller promociona lo que SÍ se descargó. Antes se hacía
    # `raise`, el `except` del artista saltaba y el `finally` borraba TODO el temp →
    # se perdían cientos de pistas buenas por una sola mala.
    if returncode != 0 and success:
        logger.warning(
            f"⚠️ yt-dlp terminó con código {returncode} (fallos parciales; se conserva "
            f"lo descargado). Última señal: {detected_error or 'ninguna'}"
        )
        success = False

    return full_output, (success, critical), detected_error, returncode

