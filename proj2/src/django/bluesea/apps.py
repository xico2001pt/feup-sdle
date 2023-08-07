from django.apps import AppConfig
import os
import sys
from loguru import logger


class BlueseaConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "bluesea"


    def setup_logger(self):
        logger_format = (
                "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
                "<level>{level: <8}</level> | "
                "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
                "<magenta>{extra[port]}</magenta> - <level>{message}</level>"
            )
        logger.configure(extra={"port": os.getenv("BLUESEA_PORT")})
        logger.remove()
        logger.add(sys.stderr, format=logger_format)


    def ready(self):
        from .scheduler import Scheduler
        from .crypto import generate_keys_if_not_exists
        
        if os.environ.get('RUN_MAIN'):
            self.setup_logger()
            generate_keys_if_not_exists()
            Scheduler().start()