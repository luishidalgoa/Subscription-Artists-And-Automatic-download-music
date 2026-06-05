# app/presentation/commands/version.py
import os
import sys

from src.domain.base_command import BaseCommand

DESCRIPCION = "Muestra la versión de yt-subs, la de yt-dlp y los metadatos del build."


def _ytdlp_version() -> str:
    """Versión del paquete yt-dlp instalado (el mismo que usa el binario)."""
    try:
        from yt_dlp.version import __version__ as v
        return v
    except Exception:
        return "desconocida"


class VersionCommand(BaseCommand):
    DESCRIPCION = DESCRIPCION
    ARGUMENTOS = {}  # sin parámetros

    def handle(self, parsed_args):
        # Estos los inyecta el build (ver Dockerfile / docker-publish.yml); en local valen
        # los valores por defecto (dev / unknown).
        print(f"yt-subs   {os.getenv('APP_VERSION', 'dev')}")
        print(f"commit    {os.getenv('APP_COMMIT', 'unknown')}")
        print(f"build     {os.getenv('APP_BUILD_TIME', 'unknown')}")
        print(f"yt-dlp    {_ytdlp_version()}")
        print(f"python    {sys.version.split()[0]}")
