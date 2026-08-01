import os
from unittest.mock import patch

from fastapi.testclient import TestClient
import pytest

os.environ["LYZR_API_KEY"] = "test_lyzr_api_key_2026"
os.environ["LLM_API_KEY"] = "test_llm_api_key_2026"
os.environ["SAFETY_SUB_AGENT_URL"] = "http://localhost:8011"

from src.extractor import perform_quote_grounded_extraction
from src.llm_client import LLMInvalidResponseError, LLMUnavailableError
from src.main import app

client = TestClient(app)


def test_extraction_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["confidence_threshold"] == 0.70


def test_valid_clinical_document_extraction_and_fhir():
    sample_text = (
        "Patient ID: PAT-10021\n"
        "Diagnosis: Diabetes Mellitus (ICD-10: E11) - High Confidence\n"
        "Medication: Metformin 500mg oral daily (RxNorm: 861004)\n"
        "Lab: HbA1c 6.8 % (LOINC: 4548-4)"
    )

    mock_llm_payload = {
        "patient_id": {"value": "PAT-10021", "literal_quote": "Patient ID: PAT-10021", "confidence": 0.95},
        "diagnoses": [
            {"name": {"value": "Diabetes Mellitus", "literal_quote": "Diabetes Mellitus", "confidence": 0.90}, "icd10_code": {"value": "E11", "literal_quote": "ICD-10: E11", "confidence": 0.90}}
        ],
        "medications": [
            {
                "name": {"value": "Metformin 500mg oral daily", "literal_quote": "Metformin 500mg oral daily", "confidence": 0.92},
                "rxnorm_code": {"value": "861004", "literal_quote": "RxNorm: 861004", "confidence": 0.92},
                "dosage": {"value": "500mg oral daily", "literal_quote": "500mg oral daily", "confidence": 0.92},
            }
        ],
        "labs": [
            {
                "name": {"value": "HbA1c", "literal_quote": "HbA1c 6.8 %", "confidence": 0.88},
                "loinc_code": {"value": "4548-4", "literal_quote": "LOINC: 4548-4", "confidence": 0.88},
                "value": {"value": "6.8 %", "literal_quote": "6.8 %", "confidence": 0.88},
            }
        ],
    }

    with patch("src.llm_client.call_llm_extraction", return_value=mock_llm_payload):
        response = client.post("/extract", json={"document_id": "DOC-TEST-100", "ocr_text": sample_text})

        assert response.status_code == 200
        data = response.json()
        assert data["document_id"] == "DOC-TEST-100"

        extracted = data["extracted_data"]
        assert extracted["patient_id"]["value"] == "PAT-10021"
        assert extracted["patient_id"]["confidence"] >= 0.70
        assert extracted["patient_id"]["literal_quote"] == "Patient ID: PAT-10021"

        fhir_res = data["fhir_resources"]
        assert len(fhir_res) >= 3
        resource_types = [r["resourceType"] for r in fhir_res]
        assert "Patient" in resource_types
        assert "Condition" in resource_types
        assert "MedicationStatement" in resource_types


def test_deliberately_ambiguous_document_triggers_incomplete():
    """Test F7: Low confidence extraction returns Incomplete."""
    ambiguous_llm_payload = {
        "patient_id": {"value": "PAT-UNKNOWN", "literal_quote": "Patient ID: PAT-UNKNOWN", "confidence": 0.30},
        "diagnoses": [
            {"name": {"value": "Unclear blurry text", "literal_quote": "Unclear blurry text", "confidence": 0.30}, "icd10_code": {"value": "I10", "literal_quote": "ICD-10: I10", "confidence": 0.30}}
        ],
        "medications": [],
        "labs": [],
    }

    with patch("src.llm_client.call_llm_extraction", return_value=ambiguous_llm_payload):
        result = perform_quote_grounded_extraction(ocr_text="Ambiguous text sample", threshold_override=0.70)

        assert result.patient_id.value == "Incomplete"
        assert result.patient_id.confidence < 0.70

        assert len(result.diagnoses) > 0
        diag = result.diagnoses[0]
        assert diag.name.value == "Incomplete"
        assert diag.name.confidence < 0.70


def test_extraction_llm_failure_produces_no_clinical_values():
    """Test F5: Extraction LLM failure produces no patient or clinical values."""
    with patch("src.llm_client.call_llm_extraction", side_effect=LLMUnavailableError("LLM API endpoint offline")):
        response = client.post("/extract", json={"document_id": "DOC-FAIL-001", "ocr_text": "Sample text"})
        assert response.status_code == 503
        assert "LLM Service Unavailable" in response.json()["detail"]


def test_invalid_extraction_json_fails_honestly():
    """Test F6: Invalid extraction JSON fails honestly with non-2xx status."""
    with patch("src.llm_client.call_llm_extraction", side_effect=LLMInvalidResponseError("Malformed JSON")):
        response = client.post("/extract", json={"document_id": "DOC-FAIL-002", "ocr_text": "Sample text"})
        assert response.status_code == 502
        assert "LLM Invalid Response" in response.json()["detail"]
