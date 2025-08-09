# app/scheduler.py
import schedule
import time
from app.controller.download_controller import run_descargas
from app.config import SCHEDULE_INTERVAL_DAYS, update_now
from app.service.yt_dlp import actualizar_yt_dlp

def update_yt_dlp_job():
    actualizar_yt_dlp()

def download_job():
    update_now()
    run_descargas()


def start_scheduler():
    schedule.every().day.do(update_yt_dlp_job)  # Actualiza yt-dlp cada día
    schedule.every(SCHEDULE_INTERVAL_DAYS).days.do(download_job)  # Descarga cada N días

    while True:
        schedule.run_pending()
        time.sleep(1)
