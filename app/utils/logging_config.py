# utils/logging_config.py
import logging
import sys

def configurar_logging():
    logging.basicConfig(
        level=logging.DEBUG,  # Cambia a DEBUG si quieres más detalle
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    logging.getLogger("musicbrainzngs").setLevel(logging.WARNING)
