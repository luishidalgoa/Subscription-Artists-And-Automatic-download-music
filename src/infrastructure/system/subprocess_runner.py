import subprocess
from typing import Callable, List, Tuple, Optional

from src.application.providers.logger_provider import LoggerProvider

logger = LoggerProvider()

def run_subprocess_with_detectors(
    command: List[str],
    detectors: List[Callable[[str], bool]],
) -> Tuple[str, bool, Optional[str], int]:
    """
    Ejecuta un comando en subprocess y lee línea por línea en streaming.

    Args:
        command: lista de argumentos del comando.
        detectors: lista de funciones detectoras que reciben cada línea.

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

    for line in process.stdout:
        line = line.strip()
        if line:
            output_lines.append(line)

            for detector in detectors:
                if detector(line):
                    detected_error = line
                    success = False
                    process.terminate()
                    process.wait()
                    break

        if not success:
            break

    process.wait()
    full_output = "\n".join(output_lines)

    # 🔹 Captura errores desconocidos
    if process.returncode != 0 and success:
        raise RuntimeError(f"⚠️ Comando falló con código {process.returncode} pero ningún detector lo reconoció: {detected_error}")

    return full_output, success, detected_error

