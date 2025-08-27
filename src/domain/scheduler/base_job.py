from abc import ABC, abstractmethod
from src.domain.scheduler.time_unit import TimeUnit

class BaseJob(ABC):
    def __init__(self, name: str, time_unit: TimeUnit, interval: int = 1,id:str|None=None):
        self.id = None
        self.name = name
        self.time_unit = time_unit
        self.interval = interval

    @abstractmethod
    def run(self):
        """Lógica que ejecuta el job"""
        pass

    def get_name(self) -> str:
        return self.name

    def get_time_unit(self) -> TimeUnit:
        return self.time_unit

    def get_interval(self) -> int:
        return self.interval
