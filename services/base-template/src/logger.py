import logging
import sys

from pythonjsonlogger import jsonlogger

from src.config import settings


def setup_logging() -> logging.Logger:
    logger = logging.getLogger(settings.service_name)

    # Avoid adding multiple handlers if setup is called multiple times
    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))

    logHandler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter(
        '%(asctime)s %(levelname)s %(name)s %(message)s',
        rename_fields={
            "levelname": "level",
            "asctime": "timestamp"
        }
    )
    logHandler.setFormatter(formatter)
    logger.addHandler(logHandler)

    return logger

logger = setup_logging()

def log_audit_event(event_type: str, user_id: str, action: str, details: dict):
    """
    Dedicated function for audit logging to ensure structured capture.
    """
    audit_data = {
        "event_type": event_type,
        "user_id": user_id,
        "action": action,
        "details": details,
        "audit": True
    }
    logger.info("Audit Event", extra=audit_data)
