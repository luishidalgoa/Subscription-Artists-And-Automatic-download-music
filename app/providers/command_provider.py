# app/providers/command_provider.py
from typing import Callable
import importlib
import pkgutil
import app.commands as commands_pkg
from app.providers.logger_provider import LoggerProvider

logger = LoggerProvider()

class Command:
    def __init__(self, name: str, description: str, action: Callable):
        self.name = name
        self.description = description
        self.action = action

class CommandProvider:
    def __init__(self):
        self.commands = []
        self.cargar_comandos()

    def register(self, command: Command):
        """Registra un comando manualmente"""
        self.commands.append(command)
        logger.info(f"Comando registrado: {command.name}")

    def get_command(self, name: str):
        """Busca un comando por nombre"""
        for cmd in self.commands:
            if cmd.name == name:
                return cmd
        return None

    def cargar_comandos(self):
        """Carga automáticamente todos los módulos en app/commands que tengan función ejecutar"""
        for _, module_name, _ in pkgutil.iter_modules(commands_pkg.__path__):
            try:
                module = importlib.import_module(f"app.commands.{module_name}")
                if hasattr(module, "ejecutar"):
                    description = getattr(module, "DESCRIPCION", "Sin descripción")
                    cmd_name = module_name.replace("_", "-")
                    self.register(Command(
                        name=cmd_name,
                        description=description,
                        action=module.ejecutar
                    ))
            except Exception as e:
                logger.error(f"No se pudo cargar el comando {module_name}: {e}")

    def listar_comandos(self):
        """Devuelve una lista de tuplas (nombre, descripción)"""
        return [(cmd.name, cmd.description) for cmd in self.commands]
