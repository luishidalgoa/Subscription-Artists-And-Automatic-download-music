from app.domain.base_command import BaseCommand
from app.application.providers.logger_provider import LoggerProvider
from app.infrastructure.service.scheduler_service import SchedulerService

logger = LoggerProvider()

class CancelJobCommand(BaseCommand):
    DESCRIPCION = "Cancela un trabajo programado del scheduler y lo borra de la base de datos"
    ARGUMENTOS = {
        "--job": {
            "params": {
                "required": True,
                "help": "Nombre del job a cancelar"
            }
        }
    }

    def handle(self, parsed_args):
        scheduler = SchedulerService()
        job = scheduler.get_job_by_name(parsed_args.job)
        scheduler.cancel_job(job)
        logger.info(f"Job canceled: {job.name}")
