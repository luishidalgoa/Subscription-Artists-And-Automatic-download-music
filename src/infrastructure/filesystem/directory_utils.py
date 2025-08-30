from pathlib import Path


def obtener_subcarpetas(directorio: Path) -> dict[str, Path]:
    """
    Devuelve un diccionario {nombre_carpeta: Path} con las subcarpetas directas.
    """
    return {carpeta.name: carpeta for carpeta in directorio.iterdir() if carpeta.is_dir()}