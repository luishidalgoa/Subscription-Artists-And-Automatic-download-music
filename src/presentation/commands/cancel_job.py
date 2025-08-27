from src.domain.base_command import BaseCommand
from src.application.providers.logger_provider import LoggerProvider
from src.infrastructure.service.scheduler_service import SchedulerService

logger = LoggerProvider()

class CancelJobCommand(BaseCommand):
    DESCRIPCION = "Cancela un trabajo programado del scheduler y lo borra de la base de datos"
    ARGUMENTOS = {
        "--job": {
            "params": {
                "required": True,
                "help": "Id del job a cancelar"
            }
        }
    }
    
    def handle(self, parsed_args):
        """
        Cancela un trabajo programado del scheduler y lo borra de la base de datos.
        
        :param parsed_args: Argumentos pasados por la linea de comandos.
        :return: None
        """
        scheduler = SchedulerService()
        job = scheduler.get_job_by_id(parsed_args.job)
        scheduler.cancel_job(job)
        logger.info(f"Job canceled: {job.id}")
