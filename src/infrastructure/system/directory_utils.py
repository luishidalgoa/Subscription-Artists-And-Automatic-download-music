from pathlib import Path

from src.infrastructure.config import file_music_extension


def obtener_subcarpetas(directorio: Path) -> dict[str, Path]:
    """
    Devuelve un diccionario {nombre_carpeta: Path} con las subcarpetas directas.
    """
    return {carpeta.name: carpeta for carpeta in directorio.iterdir() if carpeta.is_dir()}

def extract_files(ruta: Path):
    songs_files = sorted(
        p for ext in file_music_extension.file_music_extension for p in ruta.glob(f"*{ext}")
    )
    if not songs_files:
        return []
    return songs_files