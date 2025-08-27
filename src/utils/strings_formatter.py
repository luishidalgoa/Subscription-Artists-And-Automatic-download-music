import re


def sanitize_path_component(name: str) -> str:
    # Eliminar caracteres no permitidos en la mayoría de FS
    name = re.sub(r'[<>:"/\\|?*\x00-\x1F]', "_", name)
    # Eliminar espacios o puntos al final
    name = name.strip().rstrip(".")
    # Evitar nombres reservados de Windows (CON, AUX, NUL, COM1, LPT1, etc.)
    reserved = {
        "CON", "PRN", "AUX", "NUL",
        *(f"COM{i}" for i in range(1, 10)),
        *(f"LPT{i}" for i in range(1, 10)),
    }
    if name.upper() in reserved:
        name = f"_{name}_"
    # Limitar longitud máxima (255)
    return name[:255]