#app
import argparse
from abc import ABC, abstractmethod

class BaseCommand(ABC):
    """
    Clase base para todos los comandos de la CLI.
    Permite definir los argumentos mediante un diccionario.
    """

    DESCRIPCION: str = "Sin descripción"
    ARGUMENTOS: dict = {}  # formato: { "nombre": { "params": {...} } }

    def __init__(self):
        # Creamos el parser automáticamente
        self.parser = argparse.ArgumentParser(description=self.DESCRIPCION)
        for arg_name, arg_data in self.ARGUMENTOS.items():
            params = arg_data.get("params", {})
            self.parser.add_argument(arg_name, **params)

    def parse(self, args):
        """Parsea los argumentos que llegan desde CLIProvider"""
        return self.parser.parse_args(args)

    @abstractmethod
    def handle(self, parsed_args):
        """Método que implementa la lógica del comando"""
        pass

    def ejecutar(self, args):
        """Método que CLIProvider llamará"""
        parsed_args = self.parse(args)
        return self.handle(parsed_args)
