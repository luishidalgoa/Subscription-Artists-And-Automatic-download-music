# app/presentation/commands/update_app.py
from app.domain.base_command import BaseCommand
from app.infrastructure.service.update_service import actualizar_app
from app.application.providers.logger_provider import LoggerProvider

logger = LoggerProvider()

DESCRIPCION = "Actualiza la aplicación a la última versión disponible en el repositorio."

class UpdateAppCommand(BaseCommand):
    DESCRIPCION = DESCRIPCION
    ARGUMENTOS = {}  # Sin parámetros

    def handle(self, parsed_args):
        actualizar_app()
