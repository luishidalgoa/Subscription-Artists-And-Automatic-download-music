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

from src.domain.scheduler.time_unit import TimeUnit
def convert_timeUnit_to_seconds(value: int, unit: TimeUnit) -> int:
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