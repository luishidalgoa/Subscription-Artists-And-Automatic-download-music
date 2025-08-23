DESCRIPCION = "Procesa todos los albumes o singles descargados de los artistas de artists.json"
from app.service.album_postprocessor import procesar_albumes
from app.config import ARTISTS_FILE
from app.providers.logger_provider import LoggerProvider
import json
from app.config import ROOT_PATH

logger = LoggerProvider()

def ejecutar():    
    """
    Procesa todos los albumes o singles descargados de los artistas de artists.json
    """
    try:
        with ARTISTS_FILE.open() as f:
            artists = json.load(f)
    except Exception as e:
        logger.error(f"Error al leer artists.json: {e}")
        return
    
    for artist in artists:
        name = artist["name"]
        output_path = ROOT_PATH / name
        procesar_albumes(output_path,{"filter_by_date": False})
