# src/infrastructure/audio/handler_factory.py
from src.infrastructure.audio.base_audio_handler import BaseAudioHandler
from src.infrastructure.audio.mp3_handler import MP3Handler
from src.infrastructure.audio.m4a_handler import M4AHandler

class AudioHandlerFactory:
    handlers = {
        "mp3": MP3Handler(),
        "m4a": M4AHandler()
    }

    @classmethod
    def get_handler(cls, ext: str)-> BaseAudioHandler:
        return cls.handlers.get(ext.lower())
