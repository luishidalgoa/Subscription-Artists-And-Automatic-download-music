DESCRIPCION = "Actualiza la aplicación a la última versión disponible en el repositorio."

from app.providers.logger_provider import LoggerProvider
from app.service.update_service import actualizar_app

logger = LoggerProvider ()

def ejecutar():
    
    logger.info("🔄 Actualizando la aplicación...")
    actualizar_app()
