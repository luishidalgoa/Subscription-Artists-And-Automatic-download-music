# src/infrastructure/audio/mp3_handler.py
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3
from mutagen.id3 import ID3NoHeaderError, ID3
from src.infrastructure.audio.base_audio_handler import BaseAudioHandler
from src.domain.Metadata import Metadata
from src.application.providers.logger_provider import LoggerProvider

logger = LoggerProvider()

class MP3Handler(BaseAudioHandler):
    def extract_comment(self, song_path: str) -> str:
        try:
            try:
                audio_easy = EasyID3(song_path)
                v = audio_easy.get("comment")
                if v:
                    return next((c for c in v if "youtube.com/watch?v=" in c), "")
            except ID3NoHeaderError:
                pass

            id3 = ID3(song_path)
            for c in id3.getall("COMM"):
                for t in c.text:
                    if "youtube.com/watch?v=" in t:
                        return t

            for t in id3.getall("TXXX"):
                if t.desc and t.desc.lower() in ("comment", "comments"):
                    for x in t.text:
                        if "youtube.com/watch?v=" in x:
                            return x
            return ""
        except Exception as e:
            logger.error(f"[comment-mp3] Error leyendo {song_path}: {e}")
            return ""

    def open_file(self, song_path: str):
        try:
            return EasyID3(song_path)
        except ID3NoHeaderError:
            audio = MP3(song_path, ID3=EasyID3)
            audio.add_tags()
            return EasyID3(song_path)

    def _apply_metadata_impl(self, audio, metadata_obj: Metadata, tags_to_extract: list, artist: str = None):
        if artist:
            audio["albumartist"] = artist
        for tag in tags_to_extract:
            value = getattr(metadata_obj, tag, None)
            if value is not None:
                audio[tag.lower()] = str(value)