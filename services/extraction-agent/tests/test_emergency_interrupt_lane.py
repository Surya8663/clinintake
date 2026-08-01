from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
import pytest

from src.main import app
from src.models import LyzrDiagnosisResponse, LyzrExtractionResponse, LyzrFieldResponse

client = TestClient(app)


def test_emergency_safety_sub_agent_evaluation_success():
    """Verifies successful direct call to Safety Sub-Agent."""
    payload = {"document_id": "DOC-EMERG-001", "ocr_text": "PAT-9901 has severe chest pain and dyspnea."}

    mock_llm_result = LyzrExtractionResponse(
        patient_id=LyzrFieldResponse(value="PAT-9901", literal_quote="PAT-9901", confidence=0.95),
        diagnoses=[
            LyzrDiagnosisResponse(
                name=LyzrFieldResponse(value="Chest Pain", literal_quote="chest pain", confidence=0.9),
                icd10_code=LyzrFieldResponse(value="", literal_quote="", confidence=0.0),
            )
        ],
        medications=[],
        labs=[],
    )

    mock_safety_resp = MagicMock()
    mock_safety_resp.status_code = 200
    mock_safety_resp.json.return_value = {
        "document_id": "DOC-EMERG-001",
        "is_emergency": True,
        "assessment_status": "complete",
        "rationale": "Severe acute chest pain",
        "latency_ms": 15.2,
    }

    with patch("src.llm_client.call_llm_extraction", return_value=mock_llm_result):
        with patch("httpx.AsyncClient.post", return_value=mock_safety_resp):
            response = client.post("/extract", json=payload)
            assert response.status_code == 200
            data = response.json()
            assert data["safety_interrupt_triggered"] is True
            assert data["safety_response"]["is_emergency"] is True
