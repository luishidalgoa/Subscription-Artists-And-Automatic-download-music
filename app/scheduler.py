# app/scheduler.py
import schedule
import time
from app.controller.download_controller import run_descargas
from app.config import SCHEDULE_INTERVAL_DAYS, update_now as update_time_now
from app.service.update_service import actualizar_app

def download_job():
    actualizar_app()
    update_time_now()
    run_descargas()

def start_scheduler():
    """Limpia los jobs y reprograma el scheduler a partir de ahora"""
    schedule.clear()
    schedule.every().day.do(actualizar_app)  # Actualiza yt-dlp cada día
    schedule.every(SCHEDULE_INTERVAL_DAYS).days.do(download_job)  # Descarga cada N días

    while True:
        schedule.run_pending()
        time.sleep(1)
        