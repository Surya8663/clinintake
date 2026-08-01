import os
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient
import httpx
from pydantic import ValidationError
import pytest

from src.extractor import create_grounded_field, locate_bbox_for_quote
from src.main import app
from src.models import LyzrExtractionResponse, LyzrFieldResponse

client = TestClient(app)


def test_missing_ocr_boxes_never_produces_fabricated_coordinates():
    """Condition 5: Missing OCR boxes returns None/empty bbox and 'spatial_data_unavailable' status."""
    bbox, status = locate_bbox_for_quote("Essential Hypertension", ocr_words=None)
    assert bbox is None
    assert status == "spatial_data_unavailable"
    assert bbox != [0, 0, 0, 0]
    assert bbox != [0, 0, 100, 20]
    assert bbox != [40, 50, 250, 70]


def test_partial_ocr_token_matches_are_not_treated_as_exact_grounding():
    """Condition 6: Partial token match (e.g. 'chest' inside 'chestnut') is rejected."""
    ocr_words = [{"text": "chestnut", "bbox": {"x_min": 10, "y_min": 10, "x_max": 50, "y_max": 30}}]
    bbox, status = locate_bbox_for_quote("chest", ocr_words=ocr_words)
    assert bbox is None
    assert status == "quote_not_located"


def test_missing_required_lyzr_agent_id_causes_startup_validation_failure():
    """Condition 4: Missing required Lyzr agent ID causes BaseSettings validation failure."""
    from src.config import Settings

    with patch.dict(os.environ, {"LYZR_API_KEY": "key", "LYZR_BASE_URL": "http://api", "LYZR_EXTRACTION_AGENT_ID": ""}):
        with pytest.raises(ValidationError):
            Settings(lyzr_extraction_agent_id="")


def test_safety_service_failure_returns_non_2xx_and_fails_closed():
    """Condition 1: Safety service connection failure returns HTTP 503 and fails closed without local safety assessment."""
    payload = {"document_id": "DOC-SAFETY-FAIL", "ocr_text": "Patient with severe chest pain and cyanosis."}

    mock_llm_payload = LyzrExtractionResponse(
        patient_id=LyzrFieldResponse(value="PAT-999", literal_quote="Patient", confidence=0.9),
        diagnoses=[],
        medications=[],
        labs=[],
    )

    with patch("src.llm_client.call_llm_extraction", return_value=mock_llm_payload):
        with patch("httpx.AsyncClient.post", side_effect=httpx.ConnectError("Connection refused")):
            response = client.post("/extract", json=payload)
            assert response.status_code == 503
            assert "Safety Sub-Agent Unavailable" in response.json()["detail"]


def test_safety_response_missing_is_emergency_is_rejected():
    """Condition 7: Safety response missing is_emergency boolean field is rejected with 502."""
    payload = {"document_id": "DOC-SAFETY-MISSING-EMERGENCY", "ocr_text": "Patient with hypertension."}

    mock_llm_payload = LyzrExtractionResponse(
        patient_id=LyzrFieldResponse(value="PAT-111", literal_quote="Patient", confidence=0.9),
        diagnoses=[],
        medications=[],
        labs=[],
    )

    mock_safety_res = MagicMock()
    mock_safety_res.status_code = 200
    mock_safety_res.json.return_value = {
        "document_id": "DOC-SAFETY-MISSING-EMERGENCY",
        "assessment_status": "complete",
        "rationale": "Evaluated",
        "latency_ms": 12.5,
    }

    with patch("src.llm_client.call_llm_extraction", return_value=mock_llm_payload):
        with patch("httpx.AsyncClient.post", return_value=mock_safety_res):
            response = client.post("/extract", json=payload)
            assert response.status_code == 502
            assert "Safety Sub-Agent Error" in response.json()["detail"]


def test_safety_response_with_is_emergency_string_is_rejected():
    """Condition 8: Safety response with truthy string is_emergency='false' is rejected."""
    payload = {"document_id": "DOC-SAFETY-STRING", "ocr_text": "Patient with hypertension."}

    mock_llm_payload = LyzrExtractionResponse(
        patient_id=LyzrFieldResponse(value="PAT-111", literal_quote="Patient", confidence=0.9),
        diagnoses=[],
        medications=[],
        labs=[],
    )

    mock_safety_res = MagicMock()
    mock_safety_res.status_code = 200
    mock_safety_res.json.return_value = {
        "document_id": "DOC-SAFETY-STRING",
        "is_emergency": "false",
        "assessment_status": "complete",
        "rationale": "Evaluated",
        "latency_ms": 12.5,
    }

    with patch("src.llm_client.call_llm_extraction", return_value=mock_llm_payload):
        with patch("httpx.AsyncClient.post", return_value=mock_safety_res):
            response = client.post("/extract", json=payload)
            assert response.status_code == 502
            assert "Safety Sub-Agent Error" in response.json()["detail"]


def test_mismatched_safety_document_id_is_rejected():
    """Condition 9: Mismatched safety document_id is rejected with 502."""
    payload = {"document_id": "DOC-SAFETY-CORRECT", "ocr_text": "Patient with hypertension."}

    mock_llm_payload = LyzrExtractionResponse(
        patient_id=LyzrFieldResponse(value="PAT-111", literal_quote="Patient", confidence=0.9),
        diagnoses=[],
        medications=[],
        labs=[],
    )

    mock_safety_res = MagicMock()
    mock_safety_res.status_code = 200
    mock_safety_res.json.return_value = {
        "document_id": "DOC-SAFETY-MISMATCHED-WRONG",
        "is_emergency": False,
        "assessment_status": "complete",
        "rationale": "Evaluated",
        "latency_ms": 12.5,
    }

    with patch("src.llm_client.call_llm_extraction", return_value=mock_llm_payload):
        with patch("httpx.AsyncClient.post", return_value=mock_safety_res):
            response = client.post("/extract", json=payload)
            assert response.status_code == 502
            assert "Safety evaluation document_id mismatch" in response.json()["detail"]
