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
from src.models import LyzrFieldResponse


def test_confidence_below_0_or_above_1_rejected():
    """Condition 6: Confidence below 0.0 or above 1.0 is rejected by schema validator."""
    with pytest.raises(ValidationError):
        LyzrFieldResponse(value="Test", literal_quote="Test", confidence=1.5)

    with pytest.raises(ValidationError):
        LyzrFieldResponse(value="Test", literal_quote="Test", confidence=-0.1)


def test_malformed_nested_extraction_data_rejected():
    """Condition 7: Malformed nested extraction structure raises LLMInvalidResponseError."""
    ocr_text = "Patient ID: PAT-123. Diagnosis: Hypertension."
    malformed_json_response = {
        "patient_id": "PAT-123",  # Invalid: Should be dict with value, literal_quote, confidence
        "diagnoses": "Hypertension",  # Invalid: Should be list of dicts
    }

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"response": malformed_json_response}

    with patch("httpx.Client.post", return_value=mock_resp):
        with pytest.raises(LLMInvalidResponseError):
            call_llm_extraction(ocr_text=ocr_text)


def test_http_429_and_5xx_retry_only_up_to_configured_limit():
    """Condition 8: HTTP 429 and 5xx errors retry up to lyzr_max_retries before failing."""
    ocr_text = "Patient ID: PAT-100"

    mock_500_resp = MagicMock()
    mock_500_resp.status_code = 500
    mock_500_resp.text = "Internal Server Error"

    with patch("httpx.Client.post", return_value=mock_500_resp) as mock_post:
        with patch("time.sleep"):  # Speed up tests
            with pytest.raises(LLMServiceError):
                call_llm_extraction(ocr_text=ocr_text)

    # Initial attempt + 2 retries (lyzr_max_retries=2 in conftest) = 3 total calls
    assert mock_post.call_count == 3


def test_http_4xx_is_not_retried():
    """Condition 9: HTTP 400 client request error is NOT retried."""
    ocr_text = "Patient ID: PAT-100"

    mock_400_resp = MagicMock()
    mock_400_resp.status_code = 400
    mock_400_resp.text = "Bad Request"

    with patch("httpx.Client.post", return_value=mock_400_resp) as mock_post:
        with pytest.raises(LLMRequestError):
            call_llm_extraction(ocr_text=ocr_text)

    # Must fail immediately after 1 attempt
    assert mock_post.call_count == 1
