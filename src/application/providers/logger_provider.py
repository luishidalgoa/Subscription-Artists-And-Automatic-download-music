import logging
from src.utils.logging_config import configurar_logging

class LoggerProvider:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = logging.getLogger("app")
            if not cls._instance.handlers:
                configurar_logging()  # solo agrega handlers si no hay
        return cls._instance
