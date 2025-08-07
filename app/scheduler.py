# app/scheduler.py
import schedule
import time
from app.controller.download_controller import run_descargas
from app.config import SCHEDULE_INTERVAL_DAYS

def start_scheduler():
    schedule.every(SCHEDULE_INTERVAL_DAYS).days.do(run_descargas)
    while True:
        schedule.run_pending()
        time.sleep(1)
