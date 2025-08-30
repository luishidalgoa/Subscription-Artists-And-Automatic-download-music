# app/providers/cli_provider.py
import argparse
import sys
from src.application.providers.logger_provider import LoggerProvider
from src.application.providers.command_provider import CommandProvider
from src.domain.base_command import BaseCommand

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
        Muestra todos los comandos disponibles junto con sus parámetros y descripción.
        """
        print("\nAvailable commands:\n")

        max_name_len = max((len(cmd.name) for cmd in self.command_provider.commands), default=0)

        for cmd in self.command_provider.commands:
            name_col = cmd.name.ljust(max_name_len + 2)
            description = getattr(cmd, "description", "Sin descripción")
            print(f"{name_col} {description}")

            # Si es un BaseCommand, listamos sus argumentos
            if hasattr(cmd.action, "__self__") and isinstance(cmd.action.__self__, BaseCommand):
                base_cmd = cmd.action.__self__
                for arg_name, arg_data in base_cmd.ARGUMENTOS.items():
                    help_text = arg_data.get("params", {}).get("help", "")
                    required = arg_data.get("params", {}).get("required", False)
                    print(f"    {arg_name} (required: {required}) - {help_text}")

        print("\nUse 'yt-subs <command> [params]' to execute a command.\n")


