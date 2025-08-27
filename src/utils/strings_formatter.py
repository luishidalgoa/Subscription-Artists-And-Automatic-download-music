import re


def sanitize_path_component(name: str) -> str:
    """
    Sustituye los caracteres '/' y '\' por '_' para evitar crear subcarpetas.
    """
    return name.replace("/", "_").replace("\\", "_")
