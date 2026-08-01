from unittest.mock import patch
from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)


def test_emergency_safety_interrupt_lane_latency_sla():
    """
    CRITICAL PRD SECTION 6 TEST:
    Verifies that the direct Emergency Safety Interrupt Lane executes and returns
    within the strict < 2.0 seconds latency requirement.
    """
    emergency_text = (
        "Patient ID: PAT-EMERGENCY-911\n"
        "Diagnosis: Severe Respiratory Distress (ICD-10: J80)\n"
        "Clinical note: Patient experiencing acute chest pain, cyanosis, and severe respiratory arrest."
    )

    mock_llm_payload = {
        "patient_id": {"value": "PAT-EMERGENCY-911", "literal_quote": "Patient ID: PAT-EMERGENCY-911", "confidence": 0.95},
        "diagnoses": [{"name": {"value": "Severe Respiratory Distress", "literal_quote": "Severe Respiratory Distress", "confidence": 0.95}, "icd10_code": {"value": "J80", "literal_quote": "ICD-10: J80", "confidence": 0.95}}],
        "medications": [],
        "labs": [],
    }

    with patch("src.llm_client.call_llm_extraction", return_value=mock_llm_payload):
        response = client.post("/extract", json={"document_id": "DOC-INTERRUPT-001", "ocr_text": emergency_text})
        assert response.status_code == 200
        data = response.json()

        assert "safety_interrupt_latency_ms" in data
        latency = data["safety_interrupt_latency_ms"]

        # Must meet < 2.0 seconds (2000 ms) SLA requirement
        assert latency < 2000.0
