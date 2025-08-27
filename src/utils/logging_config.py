import logging

def configurar_logging():
    logger = logging.getLogger("app")
    if logger.handlers:  # si ya tiene handlers, salir
        return
    ch = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    logger.setLevel(logging.INFO)
