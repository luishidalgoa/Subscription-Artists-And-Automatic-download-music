# app/application/providers/command_provider.py
import importlib
import pkgutil
import inspect
from src.presentation import commands as commands_pkg
from src.application.providers.logger_provider import LoggerProvider
from src.domain.base_command import BaseCommand

logger = LoggerProvider()

class Command:
    def __init__(self, name: str, description: str, action):
        self.name = name
        self.description = description
        self.action = action  # callable, normalmente la instancia.ejecutar

class CommandProvider:
    def __init__(self):
        self.commands = []
        self.cargar_comandos()

    def register(self, command: Command):
        self.commands.append(command)

    def get_command(self, name: str):
        for cmd in self.commands:
            if cmd.name == name:
                return cmd
        return None

    def cargar_comandos(self):
        """Carga automáticamente todas las clases que hereden de BaseCommand"""
        for _, module_name, _ in pkgutil.iter_modules(commands_pkg.__path__):
            try:
                module = importlib.import_module(f"src.presentation.commands.{module_name}")
                
                # Buscamos clases que hereden de BaseCommand
                for name, cls in inspect.getmembers(module, inspect.isclass):
                    if issubclass(cls, BaseCommand) and cls is not BaseCommand:
                        instancia = cls()
                        cmd_name = module_name.replace("_", "-")
                        self.register(Command(
                            name=cmd_name,
                            description=getattr(cls, "DESCRIPCION", "Sin descripción"),
                            action=instancia.ejecutar
                        ))
            except Exception as e:
                logger.error(f"No se pudo cargar el comando {module_name}: {e}")

    def listar_comandos(self):
        return [(cmd.name, cmd.description) for cmd in self.commands]
