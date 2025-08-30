from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3
from mutagen.id3 import ID3NoHeaderError
from src.domain.base_command import BaseCommand
from src.application.providers.logger_provider import LoggerProvider
from src.infrastructure.config.config import ROOT_PATH
from src.infrastructure.filesystem.directory_utils import extract_files, obtener_subcarpetas
from src.infrastructure.filesystem.json_loader import artists_load
from src.infrastructure.service import album_postprocessor, yt_dlp_service
from src.utils.strings_formatter import sanitize_path_component
from src.domain.Metadata import Metadata

MetadataFields = list(vars(Metadata()).keys())

MetadataFields.remove("Album")
logger = LoggerProvider()


class FetchMetadataCommand(BaseCommand):
    DESCRIPCION = "Extrae metadatos de una URL de YouTube usando yt-dlp y devuelve campos seleccionados"
    ARGUMENTOS = {
        "--tags": {
            "params": {
                "required": False,
                "help": f"Lista de campos/metadatos a extraer. Campos aceptados: {', '.join(MetadataFields)}",
                "nargs": "*",
                "default": MetadataFields
            }
        },
        "--artists": {
            "params": {
                "required": False,
                "help": "Artistas a extraer: 'All' o un string específico",
                "default": "All"
            }
        }
    }

    def _extract_comment(self, song_path: str) -> str:
        """
        Extrae solo URLs válidas de YouTube desde un MP3.
        Devuelve la primera URL que contenga 'youtube.com/watch?v='.
        Si no encuentra ninguna, devuelve cadena vacía.
        """
        try:
            # 1) Intentar EasyID3
            try:
                audio_easy = EasyID3(song_path)
                v = audio_easy.get("comment")
                if v:
                    for c in v:
                        if "youtube.com/watch?v=" in c:
                            return c
            except ID3NoHeaderError:
                # MP3 sin cabecera ID3, se maneja en el siguiente paso
                pass

            # 2) Inspección ID3 "raw"
            try:
                from mutagen.id3 import ID3
                id3 = ID3(song_path)
            except Exception:
                return ""

            # COMM frames
            comms = id3.getall("COMM")
            for c in comms:
                for t in c.text:
                    if "youtube.com/watch?v=" in t:
                        return t

            # Fallback: TXXX con desc 'comment'/'comments'
            txxx_frames = id3.getall("TXXX")
            for t in txxx_frames:
                if t.desc and t.desc.lower() in ("comment", "comments"):
                    for x in t.text:
                        if "youtube.com/watch?v=" in x:
                            return x

            # Si no encontró nada válido
            return ""

        except Exception as e:
            logger.error(f"[comment] Error leyendo {song_path}: {e}")
            return ""

    def _apply_metadata(self, audio, metadata_obj, tags_to_extract, artist: str = None):
        #ponemos a fuego el albumartist si recibe artist la funcion
        if artist:
            audio["albumartist"] = artist
        for tag in tags_to_extract:
            value = getattr(metadata_obj, tag, None)
            if value is not None:
                audio[tag] = str(value)

    def handle(self, parsed_args):
        tags_to_extract = parsed_args.tags or MetadataFields
        artists_param = parsed_args.artists

        logger.info(f"Campos a extraer: {tags_to_extract}")
        logger.info(f"Parámetro de artistas: {artists_param}")

        if artists_param == "All" or not artists_param:
            for artist in artists_load():
                safe_name = sanitize_path_component(artist["name"])
                artist_root = ROOT_PATH / safe_name
                subfolders = obtener_subcarpetas(directorio=artist_root)

                for _, ruta in subfolders.items():
                    songs_files = extract_files(ruta)

                    for song in songs_files:
                        try:
                            # 1. Extraer el comentario con función privada
                            comment = self._extract_comment(song)
                            if not comment:
                                logger.warning(f"No hay URL de YouTube en el archivo: {song}")
                                continue

                            # 2. Obtener metadatos de YouTube
                            raw_metadata = yt_dlp_service.fetch_raw_metadata(comment)
                            metadata_obj = album_postprocessor.extract_metadata(raw_metadata, tags_to_extract)
                            # 3. Abrir con EasyID3 para actualizar metadatos
                            try:
                                audio = EasyID3(song)
                            except ID3NoHeaderError:
                                audio = MP3(song, ID3=EasyID3)
                                audio.add_tags()
                                audio = EasyID3(song)

                            self._apply_metadata(audio, metadata_obj, tags_to_extract, artist=artist["name"])

                            audio.save()

                        except Exception as e:
                            yt_dlp_service.flush_batch_cache()
                            logger.error(f"Error procesando archivo {song}: {e}")

                        yt_dlp_service.flush_batch_cache()
        else:
            logger.info(f"Procesando solo el artista especificado: {artists_param}")
            # Aquí iría la lógica para un artista específico