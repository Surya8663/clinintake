import os
from unittest.mock import patch

from fastapi.testclient import TestClient
import pytest

os.environ["LYZR_API_KEY"] = "test_lyzr_api_key_2026"
os.environ["LLM_API_KEY"] = "test_llm_api_key_2026"

from src.llm_client import LLMUnavailableError
from src.main import app

client = TestClient(app)


def test_referral_drafting_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_generate_referral_draft_letter():
    payload = {
        "document_id": "DOC-REF-001",
        "patient_id": "PAT-Gastro-007",
        "target_specialty": "Gastroenterology",
        "clinical_decision_package": {
            "patient_id": "PAT-Gastro-007",
            "temporal_care_gaps": [{"measure_name": "USPSTF Colorectal Screening", "status": "overdue"}],
            "guideline_passages": [
                {
                    "source": "USPSTF CRC 2021",
                    "section": "Recommendation",
                    "clause_id": "CRC-2021-01",
                    "passage_text": "The USPSTF recommends screening for colorectal cancer in adults aged 45 to 75 years.",
                }
            ],
        },
    }

    mock_letter = (
        "CLINICAL REFERRAL LETTER\n"
        "Date: 2026-08-01\n"
        "To: Department of Gastroenterology\n"
        "Re: Patient PAT-Gastro-007\n\n"
        "Dear Specialist,\n"
        "I am referring PAT-Gastro-007 for Gastroenterology evaluation due to Colorectal screening overdue."
    )

    with patch("src.drafting_engine.call_llm_referral_draft", return_value=mock_letter):
        response = client.post("/referral/draft", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["document_id"] == "DOC-REF-001"
        assert data["target_specialty"] == "Gastroenterology"
        assert len(data["referral_letter_text"]) > 50
        assert "PAT-Gastro-007" in data["referral_letter_text"]
        assert "Gastroenterology" in data["referral_letter_text"]
        assert len(data["grounded_evidence"]) == 1
        assert data["grounded_evidence"][0]["clause_id"] == "CRC-2021-01"


def test_referral_drafting_failure_produces_no_fallback_letter():
    """Test F10: Referral drafting failure produces no fallback letter and returns non-2xx HTTP status."""
    payload = {
        "document_id": "DOC-REF-FAIL",
        "patient_id": "PAT-FAIL-01",
        "target_specialty": "Neurology",
        "clinical_decision_package": {
            "patient_id": "PAT-FAIL-01",
            "temporal_care_gaps": [],
            "guideline_passages": [],
        },
    }

    with patch("src.drafting_engine.call_llm_referral_draft", side_effect=LLMUnavailableError("Referral LLM Service Unavailable")):
        response = client.post("/referral/draft", json=payload)
        assert response.status_code == 503
        assert "Referral LLM Service Unavailable" in response.json()["detail"]
