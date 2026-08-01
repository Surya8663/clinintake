from unittest.mock import patch

from fastapi.testclient import TestClient
import pytest

from src.main import app

client = TestClient(app)


def test_referral_drafting_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_missing_referral_specialty_returns_422():
    """Condition 11: Missing target_specialty in request or package returns HTTP 422."""
    payload = {
        "document_id": "DOC-MISSING-SPEC",
        "patient_id": "PAT-SPEC-01",
        "target_specialty": None,  # Missing specialty
        "clinical_decision_package": {
            "patient_id": "PAT-SPEC-01",
            "temporal_care_gaps": [{"measure_name": "Colorectal Screening", "status": "overdue"}],
        },
    }

    response = client.post("/referral/draft", json=payload)
    assert response.status_code == 422
    assert "Missing required target_specialty" in response.json()["detail"]


def test_missing_referral_clinical_reasons_returns_422():
    """Condition 12: Missing supported clinical reasons in package returns HTTP 422."""
    payload = {
        "document_id": "DOC-MISSING-REASONS",
        "patient_id": "PAT-REASON-01",
        "target_specialty": "Gastroenterology",
        "clinical_decision_package": {
            "patient_id": "PAT-REASON-01",
            "temporal_care_gaps": [],  # No care gaps
            "safety_assessment": {"is_emergency": False, "red_flags": []},  # No safety red flags
        },
    }

    response = client.post("/referral/draft", json=payload)
    assert response.status_code == 422
    assert "Missing required clinical_reasons" in response.json()["detail"]


def test_valid_referral_draft_letter_generation():
    """Verifies valid referral draft generation when specialty and reasons exist."""
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
                    "passage_text": "Screening for colorectal cancer in adults aged 45 to 75.",
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
        "Referring patient PAT-Gastro-007 for Gastroenterology evaluation due to overdue Colorectal screening."
    )

    with patch("src.drafting_engine.call_llm_referral_draft", return_value=mock_letter):
        response = client.post("/referral/draft", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["document_id"] == "DOC-REF-001"
        assert data["target_specialty"] == "Gastroenterology"
        assert "PAT-Gastro-007" in data["referral_letter_text"]
