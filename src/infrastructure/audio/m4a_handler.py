# src/infrastructure/audio/m4a_handler.py
from mutagen.mp4 import MP4
from src.infrastructure.audio.base_audio_handler import BaseAudioHandler
from src.domain.Metadata import Metadata
from src.application.providers.logger_provider import LoggerProvider

logger = LoggerProvider()

class M4AHandler(BaseAudioHandler):
    def extract_comment(self, song_path: str) -> str:
        try:
            audio = MP4(song_path)
            for key in ("©cmt", "desc"):
                if key in audio.tags:
                    return next((c for c in audio.tags[key] if "youtube.com/watch?v=" in c), "")

            for key, value in audio.tags.items():
                if key.startswith("----:") and "comment" in key.lower():
                    for c in value:
                        if isinstance(c, bytes):
                            c = c.decode(errors="ignore")
                        if "youtube.com/watch?v=" in c:
                            return c
            return ""
        except Exception as e:
            logger.error(f"[comment-m4a] Error leyendo {song_path}: {e}")
            return ""

    def open_file(self, song_path: str):
        return MP4(song_path)

    def apply_metadata(self, audio, metadata_obj: Metadata, tags_to_extract: list, artist: str = None):
        if artist:
            audio["aART"] = [artist]
        for tag in tags_to_extract:
            value = getattr(metadata_obj, tag, None)
            if value is not None:
                if tag == "Title":
                    audio["©nam"] = [str(value)]
                elif tag == "Artist":
                    audio["©ART"] = [str(value)]
                elif tag == "Date":
                    audio["©day"] = [str(value)]
