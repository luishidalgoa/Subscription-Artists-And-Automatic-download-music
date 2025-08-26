# app/providers/cli_provider.py
import argparse
import sys
from app.application.providers.logger_provider import LoggerProvider
from app.application.providers.command_provider import CommandProvider

logger = LoggerProvider()

class CLIProvider:
    def __init__(self, command_provider: CommandProvider):
        self.command_provider = command_provider

    def run(self):
        parser = argparse.ArgumentParser(description="CLI de la aplicación")
        parser.add_argument(
            "command",
            nargs="?",
            default="boot",
            help="Comando a ejecutar (por defecto: boot)"
        )
        parser.add_argument(
            "--list", "-l",
            action="store_true",
            help="Muestra todos los comandos disponibles"
        )

        # Parseamos solo los argumentos principales
        args, unknown_args = parser.parse_known_args()  # unknown_args captura los parámetros del comando

        if args.list:
            self.list_commands()
            return

        command = self.command_provider.get_command(args.command)
        if command:
            logger.info(f"Ejecutando comando: {command.name}")
            try:
                # Pasamos los parámetros restantes al comando
                command.action(unknown_args)
            except SystemExit:
                # argparse dentro del comando podría llamar a sys.exit, lo capturamos
                pass
        else:
            logger.error(f"Comando no encontrado: {args.command}")
            self.list_commands()

    def list_commands(self):
        """
        Muestra todos los comandos disponibles en formato tabulado,
        limpio, sin logs de registro repetidos.
        """
        print("\nAvailable commands:\n")
        
        max_name_len = max((len(cmd.name) for cmd in self.command_provider.commands), default=0)
        
        for cmd in self.command_provider.commands:
            name_col = cmd.name.ljust(max_name_len + 2)
            description = getattr(cmd, "description", "Sin descripción")
            print(f"{name_col} {description}")
        
        print("\nUse 'python -m app.main <command> [params]' to execute a command.\n")

