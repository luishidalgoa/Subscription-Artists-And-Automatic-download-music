# app/providers/app_provider.py
from app.providers.logger_provider import LoggerProvider
from app.providers.command_provider import CommandProvider
from app.providers.cli_provider import CLIProvider

class AppProvider:
    def __init__(self):
        # Inicializa providers
        self.logger = LoggerProvider()
        self.command_provider = CommandProvider()  # carga automáticamente todos los comandos
        self.cli_provider = CLIProvider(self.command_provider)

    def run(self):
        self.cli_provider.run()
