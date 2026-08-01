import os
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
import httpx
from pydantic import ValidationError
import pytest

from src.extractor import create_grounded_field, locate_bbox_for_quote
from src.main import app

client = TestClient(app)


def test_missing_ocr_boxes_never_produces_fabricated_coordinates():
    """Condition 2: Missing OCR boxes returns None/empty bbox and 'spatial_data_unavailable' status."""
    bbox, status = locate_bbox_for_quote("Essential Hypertension", ocr_words=None)
    assert bbox is None
    assert status == "spatial_data_unavailable"

    # Ensure no fabricated default coordinates [0, 0, 100, 20] or [40, 50, 250, 70]
    assert bbox != [0, 0, 100, 20]
    assert bbox != [40, 50, 250, 70]


def test_quote_absent_from_ocr_text_is_unsupported():
    """Condition 3: Quote absent from OCR text sets grounding_status='quote_unsupported'."""
    field = create_grounded_field(
        raw_value="Diabetes Mellitus",
        literal_quote="Diabetes Mellitus Type 2",
        confidence=0.95,
        ocr_text="Patient has Essential Hypertension.",
        ocr_words=[],
    )
    assert field.grounding_status == "quote_unsupported"
    assert field.bbox is None


def test_missing_required_lyzr_agent_id_causes_startup_validation_failure():
    """Condition 4: Missing required Lyzr agent ID causes BaseSettings validation failure."""
    from src.config import Settings

    with patch.dict(os.environ, {"LYZR_API_KEY": "key", "LYZR_BASE_URL": "http://api", "LYZR_EXTRACTION_AGENT_ID": ""}):
        with pytest.raises(ValidationError):
            Settings(lyzr_extraction_agent_id="")


def test_safety_service_failure_returns_non_2xx_and_fails_closed():
    """Condition 1: Safety service connection failure returns HTTP 503 and fails closed without local safety assessment."""
    payload = {"document_id": "DOC-SAFETY-FAIL", "ocr_text": "Patient with severe chest pain and cyanosis."}

    mock_llm_payload = {
        "patient_id": {"value": "PAT-999", "literal_quote": "PAT-999", "confidence": 0.9},
        "diagnoses": [],
        "medications": [],
        "labs": [],
    }

    with patch("src.llm_client.call_llm_extraction", return_value=mock_llm_payload):
        with patch("httpx.AsyncClient.post", side_effect=httpx.ConnectError("Connection refused")):
            response = client.post("/extract", json=payload)
            assert response.status_code == 503
            assert "Safety Sub-Agent Unavailable" in response.json()["detail"]
