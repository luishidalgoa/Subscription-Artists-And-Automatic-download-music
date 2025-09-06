# src/infrastructure/audio/base_audio_handler.py
from abc import ABC, abstractmethod
from pathlib import Path
from venv import logger
from src.domain.Metadata import Metadata

class BaseAudioHandler(ABC):

    @abstractmethod
    def extract_comment(self, song_path: str) -> str:
        """Extrae la URL de YouTube del archivo."""

    @abstractmethod
    def open_file(self, song_path: str):
        """Devuelve el objeto mutagen adecuado para edición."""

    @abstractmethod
    def _apply_metadata_impl(self, audio, metadata_obj: Metadata, tags_to_extract: list, artist: str = None):
        """Subclase implementa la aplicación de metadatos."""

    def apply_metadata(self, audio, metadata_obj: Metadata, tags_to_extract: list, artist: str = None):
        """
        Método plantilla: siempre valida antes de aplicar metadatos.
        """
        self._validate(metadata_obj)
        self._apply_metadata_impl(audio, metadata_obj, tags_to_extract, artist)

    def _validate(self, metadata_obj: Metadata):
        """
        Validación obligatoria antes de aplicar metadatos.
        """
        if not metadata_obj:
            raise ValueError("Metadata_obj no puede ser None")

        # obtener todos los atributos del objeto Metadata
        attrs = vars(metadata_obj)  # dict {nombre_atributo: valor}

        # si todos los atributos son None, hacemos return
        if not any(value is not None for value in attrs.values()):
            return

    def getMetadata(self, file: Path, tags_to_extract: list) -> Metadata:
        """
        Extrae metadatos del archivo de audio.
        """
        audio = self.open_file(file)
        metadata = Metadata()
        for tag in tags_to_extract:
            value = audio.get(tag.lower())
            if value:
                setattr(metadata, tag, value[0] if isinstance(value, list) else value)
        return metadata