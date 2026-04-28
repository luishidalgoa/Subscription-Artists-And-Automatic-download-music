import re

from src.domain.scheduler.time_unit import TimeUnit
import unicodedata

class Transform:
    def timeUnit_to_seconds(value: int, unit: TimeUnit) -> int:
        """
        Convierte de TimeUnit a segundos
        """
        if unit == TimeUnit.SECONDS:
            return value
        elif unit == TimeUnit.MINUTES:
            return value * 60
        elif unit == TimeUnit.HOURS:
            return value * 3600
        elif unit == TimeUnit.DAYS:
            return value * 86400
        else:
            raise ValueError("Unidad de tiempo no soportada")
        
    def seconds_to_ddhhmmss(seconds: float) -> str:
        """
        Convierte un número de segundos en un string con formato dd:hh:mm:ss.
        """
        if seconds < 0:
            seconds = 0
        seconds = int(seconds)
        days, rem = divmod(seconds, 86400)      # 86400 segundos en un día
        hours, rem = divmod(rem, 3600)          # 3600 segundos en una hora
        minutes, seconds = divmod(rem, 60)
        return f"{days:02}:{hours:02}:{minutes:02}:{seconds:02}"

    def normalize_date(date_val: int | str) -> str:
        """
        Normaliza un valor de fecha a formato 'YYYY-MM-DD'.
        Acepta:
        - 20250529 -> '2025-05-29'
        - 202505   -> '2025-05-01'
        - 2025     -> '2025-01-01'
        Devuelve string en formato ISO.
        """
        date_str = str(date_val)
        
        if len(date_str) == 8:  # YYYYMMDD
            return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
        elif len(date_str) == 6:  # YYYYMM
            return f"{date_str[:4]}-{date_str[4:6]}-01"
        elif len(date_str) == 4:  # YYYY
            return f"{date_str}-01-01"
        else:
            # fallback: si no es reconocible, devuelve como está
            return date_str


    @staticmethod
    def sanitize_path_component(name: str) -> str:
        """
        Limpia nombres para filesystem sin deformarlos demasiado.
        """
        if not name:
            return "Unknown"

        # Normalizar unicode (quita rarezas invisibles)
        name = unicodedata.normalize("NFKC", name)

        # Sustitucciones básicas
        name = name.replace("/", "_").replace("\\", "_")
        name = name.replace('"', "'")

        # Quitar caracteres ilegales en sistemas de archivos
        name = re.sub(r'[<>:*?|]', '', name)

        # Espacios limpios
        name = re.sub(r"\s+", " ", name).strip()

        return name

    @staticmethod
    def normalize_name(name: str) -> str:
        """
        Normaliza nombres para comparar:
        - minúsculas
        - sin acentos
        - sin símbolos raros
        - espacios unificados
        """
        name = name.lower()

        name = unicodedata.normalize("NFKD", name)
        name = "".join(c for c in name if not unicodedata.combining(c))

        name = re.sub(r"[^\w\s]", "", name)
        name = re.sub(r"\s+", " ", name).strip()

        return name

    
