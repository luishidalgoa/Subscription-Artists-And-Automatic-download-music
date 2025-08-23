# app/providers/cli_provider.py
import argparse
from app.providers.logger_provider import LoggerProvider
from app.providers.command_provider import CommandProvider

logger = LoggerProvider()

class CLIProvider:
    def __init__(self, command_provider: CommandProvider):
        self.command_provider = command_provider

    def run(self):
        parser = argparse.ArgumentParser(description="CLI de la aplicación")
        parser.add_argument(
            "command",
            nargs="?",
            default="run-now",
            help="Comando a ejecutar (por defecto: run-now)"
        )
        parser.add_argument(
            "--list", "-l",
            action="store_true",
            help="Muestra todos los comandos disponibles"
        )

        args = parser.parse_args()

        if args.list:
            self.list_commands()
            return

        command = self.command_provider.get_command(args.command)
        if command:
            logger.info(f"Ejecutando comando: {command.name}")
            command.action()
        else:
            logger.error(f"Comando no encontrado: {args.command}")
            self.list_commands()

    def list_commands(self):
        """
        Muestra todos los comandos disponibles en formato tabulado,
        limpio, sin logs de registro repetidos.
        """
        # Cabecera opcional
        print("\nAvailable commands:\n")
        
        # Calculamos ancho de la columna del nombre
        max_name_len = max((len(cmd.name) for cmd in self.command_provider.commands), default=0)
        
        for cmd in self.command_provider.commands:
            name_col = cmd.name.ljust(max_name_len + 2)
            description = getattr(cmd, "description", "Sin descripción")
            print(f"{name_col} {description}")
        
        print("\nUse 'python -m app.main <command>' to execute a command.\n")
