"""
PHI-Safe structured JSON logging formatter for all ClinIntake microservices.

Rules enforced:
- Log records may contain: IDs, hashes, states, durations, error codes, service names.
- Log records must NOT contain: patient names, dates of birth, diagnoses, clinical notes,
  medication lists, addresses, or any raw PHI fields.
- PHI is detected by field name; matching fields are replaced with [PHI_REDACTED].

Usage:
    from services.common.phi_safe_logger import configure_phi_safe_logging
    configure_phi_safe_logging()
"""
import datetime
import json
import logging
import re

# Field names whose VALUES must never appear in logs
_PHI_FIELD_NAMES = frozenset({
    "patient_name", "first_name", "last_name", "date_of_birth", "dob",
    "address", "street", "zip_code", "postal_code", "phone", "email",
    "ssn", "social_security", "diagnosis_text", "clinical_notes",
    "medication_name", "drug_name", "allergy", "source_quote",
    "passage_text",  # raw guideline text is not PHI but can contain patient-specific info
})

_PHI_PATTERN = re.compile(
    r"\b(patient_name|date_of_birth|dob|ssn|address|clinical_note)\b",
    re.IGNORECASE
)


def _redact_dict(record: dict) -> dict:
    """Recursively redact PHI field values from a log record dict."""
    sanitized = {}
    for key, value in record.items():
        if key.lower() in _PHI_FIELD_NAMES:
            sanitized[key] = "[PHI_REDACTED]"
        elif isinstance(value, dict):
            sanitized[key] = _redact_dict(value)
        elif isinstance(value, list):
            sanitized[key] = [
                _redact_dict(v) if isinstance(v, dict) else v
                for v in value
            ]
        elif isinstance(value, str) and _PHI_PATTERN.search(key):
            sanitized[key] = "[PHI_REDACTED]"
        else:
            sanitized[key] = value
    return sanitized


class PhiSafeJsonFormatter(logging.Formatter):
    """
    Formats log records as PHI-safe JSON with timestamp, level, name, message, and extras.
    """
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        }
        # Include structured extras, excluding private Python logging attributes
        for key, value in record.__dict__.items():
            if key in (
                "args", "created", "exc_info", "exc_text", "filename", "funcName",
                "levelname", "levelno", "lineno", "message", "module", "msecs",
                "msg", "name", "pathname", "process", "processName", "relativeCreated",
                "stack_info", "taskName", "thread", "threadName",
            ):
                continue
            if key.lower() in _PHI_FIELD_NAMES:
                log_entry[key] = "[PHI_REDACTED]"
            else:
                log_entry[key] = value

        return json.dumps(_redact_dict(log_entry))


def configure_phi_safe_logging(service_name: str = "clinintake-service", level: str = "INFO") -> None:
    """Configure the root logger with the PHI-safe JSON formatter."""
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    handler = logging.StreamHandler()
    handler.setFormatter(PhiSafeJsonFormatter())

    # Remove existing handlers to avoid duplicate output
    root_logger.handlers.clear()
    root_logger.addHandler(handler)

    logging.getLogger(service_name).info(
        "PHI-safe structured JSON logging configured.",
        extra={"service_name": service_name}
    )
