import logging
import sys

from pythonjsonlogger import jsonlogger

from src.config import settings


def setup_logging() -> logging.Logger:
    logger = logging.getLogger(settings.service_name)
    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))
    logHandler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter("%(asctime)s %(levelname)s %(name)s %(message)s", rename_fields={"levelname": "level", "asctime": "timestamp"})
    logHandler.setFormatter(formatter)
    logger.addHandler(logHandler)
    return logger


logger = setup_logging()
