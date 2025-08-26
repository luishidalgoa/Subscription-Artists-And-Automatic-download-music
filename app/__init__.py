# app/main.py
from app.application.scheduler import start_scheduler

if __name__ == "__main__":
    print("🕒 Servicio activo. Esperando tareas...")
    start_scheduler()

# app/scheduler.py
import schedule
import time
from app.controller.download_controller import run_descargas

def start_scheduler():
    schedule.every(1).minutes.do(run_descargas)
    while True:
        schedule.run_pending()
        time.sleep(1)