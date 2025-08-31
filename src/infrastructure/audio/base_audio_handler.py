# src/infrastructure/audio/base_audio_handler.py
from abc import ABC, abstractmethod
from src.domain.Metadata import Metadata

class BaseAudioHandler(ABC):

    @abstractmethod
    def extract_comment(self, song_path: str) -> str:
        """Extrae la URL de YouTube del archivo."""

    @abstractmethod
    def open_file(self, song_path: str):
        """Devuelve el objeto mutagen adecuado para edición."""

    @abstractmethod
    def apply_metadata(self, audio, metadata_obj: Metadata, tags_to_extract: list, artist: str = None):
        """Aplica metadatos al objeto mutagen y lo prepara para guardar."""
