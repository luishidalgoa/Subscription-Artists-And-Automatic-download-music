import subprocess
from typing import Callable, List, Tuple, Optional

from src.application.providers.logger_provider import LoggerProvider

logger = LoggerProvider()

def run_subprocess_with_detectors(
    command: List[str],
    detectors: List[Callable[[str, Optional[int]], bool]],
) -> Tuple[str, bool, Optional[str], int]:
    """
    Ejecuta un comando en subprocess y lee línea por línea en streaming.

    Args:
        command: lista de argumentos del comando.
        detectors: lista de funciones detectoras que reciben cada línea y opcionalmente el returncode.

    Returns:
        (output, success, detected_error, returncode)
          - output: salida completa del proceso (stdout+stderr).
          - success: True si terminó sin detectar errores críticos.
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

    # 🔹 Leer líneas en streaming y llamar a detectores que dependen solo de líneas
    for line in process.stdout:
        line = line.strip()
        if line:
            output_lines.append(line)
            for detector in detectors:
                detected, critical = detector(line, None)
                if detected:
                    detected_error = line
                    if critical:
                        success = False
                        process.terminate()
                        process.wait()
                        break
            if not success:
                break

    process.wait()
    returncode = process.returncode
    full_output = "\n".join(output_lines)

    # 🔹 Detectores que dependen del returncode
    if success:  # solo si no se disparó ninguno antes
        for detector in detectors:
            if detector(full_output, returncode):
                detected_error = full_output
                success = False
                break

    # 🔹 Captura errores desconocidos
    if returncode != 0 and success:
        logger.error(
            f"⚠️ Comando falló con código {returncode} "
            f"pero ningún detector lo reconoció. Salida parcial: {detected_error or 'ninguno'}, full output:\n{full_output}"
        )
        raise RuntimeError("Proceso terminado con error")

    return full_output, success, detected_error, returncode

