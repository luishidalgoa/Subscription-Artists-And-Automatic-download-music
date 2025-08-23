# app/service/download_service.py
from app.service.file_service import mover_a_albumes, eliminar_previews, renombrar_con_indice_en, actualizar_portada, obtener_subcarpetas
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import List
import time
from app.config import now
from app.providers.logger_provider import LoggerProvider

logger = LoggerProvider()

def procesar_albumes(artista_path: Path):
    mover_a_albumes(artista_path)

    time.sleep(2)
    subcarpetas = obtener_subcarpetas(artista_path)

    for _, ruta in subcarpetas.items():
        mp3s = sorted(ruta.glob("*.mp3"))
        if not mp3s:
            continue

        mp3s_a_procesar = filtrar_mp3s_por_fecha(mp3s, now, margen_minutos=5)
        if mp3s_a_procesar:

            eliminar_previews(mp3s_a_procesar)
            mp3s_a_procesar = renombrar_con_indice_en(mp3s_a_procesar, artista_path.name)
            actualizar_portada(mp3s_a_procesar, artista_path.name)

def filtrar_mp3s_por_fecha(mp3s: List[Path], referencia_iso: str, margen_minutos: int = 5) -> List[Path]:
    referencia_dt = datetime.fromisoformat(referencia_iso).replace(tzinfo=timezone.utc)
    limite_inferior = referencia_dt - timedelta(minutes=margen_minutos)
    filtrados = []
    for mp3 in mp3s:
        mtime = datetime.fromtimestamp(mp3.stat().st_mtime, tz=timezone.utc)
        if mtime >= limite_inferior:
            filtrados.append(mp3)
    return filtrados

    #temp= []
    #for mp3 in mp3s:
    #    from app.utils.audio_utils import extraer_album, normalize_to_ascii
    #    # extraemos el metadato album
    #    album = extraer_album(mp3)
    #        
    #    if not normalize_to_ascii(album) == normalize_to_ascii("emails i can’t send fwd："):
    #        logger.warning("No es el album que buscamos")
    #        return None
    #    temp.append(mp3)
    #return temp

    #return mp3s
