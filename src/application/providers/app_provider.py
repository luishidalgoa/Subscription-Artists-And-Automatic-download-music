# app/providers/app_provider.py
from src.application.providers.logger_provider import LoggerProvider
from src.application.providers.command_provider import CommandProvider
from src.application.providers.cli_provider import CLIProvider


class AppProvider:
    def __init__(self):
        # Inicializa providers
        self.logger = LoggerProvider()
        self.command_provider = CommandProvider()  # carga automáticamente todos los comandos
        self.cli_provider = CLIProvider(self.command_provider)

    def run(self):
        self.cli_provider.run()
