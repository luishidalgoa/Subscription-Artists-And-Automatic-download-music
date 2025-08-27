# app/domain/job.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Job:
    id: str
    name: str
    next_run_time: Optional[datetime]
    last_run_time: Optional[datetime]
    is_resumed: bool = False
