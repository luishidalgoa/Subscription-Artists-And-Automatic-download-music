# app/providers/logger_provider.py
import logging
from app.utils.logging_config import configurar_logging

class LoggerProvider:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            configurar_logging()
            cls._instance = logging.getLogger("app")
        return cls._instance
