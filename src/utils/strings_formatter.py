import re


def sanitize_path_component(name: str) -> str:
    """
    Sustituye:
      - '/' y '\' por '_' para evitar crear subcarpetas.
      - '"' por "'" para evitar problemas en nombres de archivo/carpeta.
    """
    return name.replace("/", "_").replace("\\", "_").replace('"', "'")
