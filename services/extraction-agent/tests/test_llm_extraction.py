from unittest.mock import MagicMock, patch

import httpx
from pydantic import ValidationError
import pytest

from src.llm_client import (
    LLMInvalidResponseError,
    LLMRequestError,
    LLMServiceError,
    LLMTimeoutError,
    LLMUnavailableError,
    call_llm_extraction,
)
from src.models import LyzrExtractionResponse, LyzrFieldResponse


def test_unexpected_top_level_extraction_fields_rejected():
    """Condition 1: Unexpected top-level fields are rejected by ConfigDict(extra='forbid')."""
    raw_payload = {
        "patient_id": {"value": "PAT-100", "literal_quote": "PAT-100", "confidence": 0.9},
        "diagnoses": [],
        "medications": [],
        "labs": [],
        "unexpected_extra_field": "forbidden_data",  # Forbidden extra field
    }
    with pytest.raises(ValidationError):
        LyzrExtractionResponse.model_validate(raw_payload)


def test_unexpected_nested_extraction_fields_rejected():
    """Condition 2: Unexpected nested fields in GroundedField are rejected by ConfigDict(extra='forbid')."""
    raw_field = {
        "value": "PAT-100",
        "literal_quote": "PAT-100",
        "confidence": 0.9,
        "unexpected_nested_field": "forbidden",
    }
    with pytest.raises(ValidationError):
        LyzrFieldResponse.model_validate(raw_field)


def test_supported_value_with_empty_literal_quote_rejected():
    """Condition 3: Non-empty supported value with empty literal_quote is rejected."""
    raw_field = {
        "value": "Essential Hypertension",
        "literal_quote": "",  # Empty quote
        "confidence": 0.9,
    }
    with pytest.raises(ValidationError):
        LyzrFieldResponse.model_validate(raw_field)


def test_empty_value_with_nonzero_confidence_rejected():
    """Condition 4: Empty value ('') with non-zero confidence (e.g. 0.8) is rejected."""
    raw_field = {
        "value": "",
        "literal_quote": "",
        "confidence": 0.8,  # Must be 0.0 for empty value
    }
    with pytest.raises(ValidationError):
        LyzrFieldResponse.model_validate(raw_field)


def test_confidence_below_0_or_above_1_rejected():
    with pytest.raises(ValidationError):
        LyzrFieldResponse(value="Test", literal_quote="Test", confidence=1.5)

    with pytest.raises(ValidationError):
        LyzrFieldResponse(value="Test", literal_quote="Test", confidence=-0.1)


def test_malformed_nested_extraction_data_rejected():
    ocr_text = "Patient ID: PAT-123. Diagnosis: Hypertension."
    malformed_json_response = {
        "patient_id": "PAT-123",
        "diagnoses": "Hypertension",
    }

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"response": malformed_json_response}

    with patch("httpx.Client.post", return_value=mock_resp):
        with pytest.raises(LLMInvalidResponseError):
            call_llm_extraction(ocr_text=ocr_text)


def test_http_429_and_5xx_retry_only_up_to_configured_limit():
    ocr_text = "Patient ID: PAT-100"

    mock_500_resp = MagicMock()
    mock_500_resp.status_code = 500
    mock_500_resp.text = "Internal Server Error"

    with patch("httpx.Client.post", return_value=mock_500_resp) as mock_post:
        with patch("time.sleep"):
            with pytest.raises(LLMServiceError):
                call_llm_extraction(ocr_text=ocr_text)

    assert mock_post.call_count == 3


def test_http_4xx_is_not_retried():
    ocr_text = "Patient ID: PAT-100"

    mock_400_resp = MagicMock()
    mock_400_resp.status_code = 400
    mock_400_resp.text = "Bad Request"

    with patch("httpx.Client.post", return_value=mock_400_resp) as mock_post:
        with pytest.raises(LLMRequestError):
            call_llm_extraction(ocr_text=ocr_text)

    assert mock_post.call_count == 1
