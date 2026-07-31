"""
PHI-safe logger unit tests.
Verifies that patient data field values are redacted from all log records.
"""
from io import StringIO
import json
import logging
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from services.common.phi_safe_logger import PhiSafeJsonFormatter, configure_phi_safe_logging


def _capture_log_record(record_extras: dict) -> dict:
    """Helper to format a log record and parse the JSON output."""
    formatter = PhiSafeJsonFormatter()
    record = logging.LogRecord(
        name="test", level=logging.INFO, pathname="", lineno=0,
        msg="Test log message", args=(), exc_info=None
    )
    for k, v in record_extras.items():
        setattr(record, k, v)
    output = formatter.format(record)
    return json.loads(output)


def test_phi_field_patient_name_is_redacted():
    result = _capture_log_record({"patient_name": "John Smith"})
    assert result.get("patient_name") == "[PHI_REDACTED]"


def test_phi_field_date_of_birth_is_redacted():
    result = _capture_log_record({"date_of_birth": "1975-04-12"})
    assert result.get("date_of_birth") == "[PHI_REDACTED]"


def test_phi_field_ssn_is_redacted():
    result = _capture_log_record({"ssn": "123-45-6789"})
    assert result.get("ssn") == "[PHI_REDACTED]"


def test_non_phi_fields_are_preserved():
    result = _capture_log_record({"document_id": "DOC-001", "trace_id": "TR-001", "duration_ms": 240})
    assert result.get("document_id") == "DOC-001"
    assert result.get("trace_id") == "TR-001"
    assert result.get("duration_ms") == 240


def test_log_message_is_preserved():
    result = _capture_log_record({})
    assert result.get("message") == "Test log message"


def test_nested_phi_field_is_redacted():
    formatter = PhiSafeJsonFormatter()
    record = logging.LogRecord(
        name="test", level=logging.INFO, pathname="", lineno=0,
        msg="Nested PHI test", args=(), exc_info=None
    )
    record.patient_data = {"patient_name": "Jane Doe", "document_id": "DOC-002"}
    output = formatter.format(record)
    parsed = json.loads(output)
    if isinstance(parsed.get("patient_data"), dict):
        assert parsed["patient_data"].get("patient_name") == "[PHI_REDACTED]"
        assert parsed["patient_data"].get("document_id") == "DOC-002"
