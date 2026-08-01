from unittest.mock import patch

from fastapi.testclient import TestClient
import pytest

from src.main import app
from src.models import LyzrEvidenceRefResponse, LyzrReferralResponse

client = TestClient(app)


def test_referral_drafting_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_referral_without_patient_id_returns_422():
    """Condition 12: Referral request missing patient_id in request or package returns HTTP 422."""
    payload = {
        "document_id": "DOC-NO-PATIENT-ID",
        "patient_id": None,  # Missing patient_id
        "target_specialty": "Gastroenterology",
        "clinical_decision_package": {
            "patient_id": None,
            "temporal_care_gaps": [{"measure_name": "Colorectal Screening", "status": "overdue"}],
        },
    }

    response = client.post("/referral/draft", json=payload)
    assert response.status_code == 422
    assert "Missing required patient_id" in response.json()["detail"]


def test_referral_care_gap_without_measure_name_returns_422():
    """Condition 13: Due/overdue care gap missing measure_name returns HTTP 422."""
    payload = {
        "document_id": "DOC-NO-MEASURE-NAME",
        "patient_id": "PAT-GAP-001",
        "target_specialty": "Gastroenterology",
        "clinical_decision_package": {
            "patient_id": "PAT-GAP-001",
            "temporal_care_gaps": [{"status": "overdue"}],  # Omitted measure_name
        },
    }

    response = client.post("/referral/draft", json=payload)
    assert response.status_code == 422
    assert "Due or overdue care gap missing measure_name" in response.json()["detail"]


def test_referral_evidence_reference_not_present_in_supplied_evidence_rejected():
    """Condition 14: Evidence reference returned by LLM that is not in supplied package evidence is rejected."""
    payload = {
        "document_id": "DOC-UNGROUNDED-REF",
        "patient_id": "PAT-UNGROUNDED-01",
        "target_specialty": "Gastroenterology",
        "clinical_decision_package": {
            "patient_id": "PAT-UNGROUNDED-01",
            "temporal_care_gaps": [{"measure_name": "Colorectal Screening", "status": "overdue"}],
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

    # LLM returns evidence ref with ungrounded clause_id
    mock_ungrounded_response = LyzrReferralResponse(
        referral_letter_text="CLINICAL REFERRAL LETTER for Gastroenterology evaluation.",
        evidence_refs_used=[
            LyzrEvidenceRefResponse(
                clause_id="FABRICATED-CLAUSE-999",  # Not in package
                source_quote="Fabricated recommendation quote",  # Not in package
            )
        ],
    )

    with patch("src.drafting_engine.call_llm_referral_draft", return_value=mock_ungrounded_response):
        response = client.post("/referral/draft", json=payload)
        assert response.status_code == 502
        assert "not present in supplied guideline evidence" in response.json()["detail"]


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

    mock_valid_response = LyzrReferralResponse(
        referral_letter_text="CLINICAL REFERRAL LETTER\nDate: 2026-08-01\nTo: Department of Gastroenterology\nRe: Patient PAT-Gastro-007\nDear Specialist,\nReferring patient PAT-Gastro-007 for Gastroenterology evaluation due to overdue Colorectal screening.",
        evidence_refs_used=[
            LyzrEvidenceRefResponse(clause_id="CRC-2021-01", source_quote="Screening for colorectal cancer in adults aged 45 to 75.")
        ],
    )

    with patch("src.drafting_engine.call_llm_referral_draft", return_value=mock_valid_response):
        response = client.post("/referral/draft", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["document_id"] == "DOC-REF-001"
        assert data["target_specialty"] == "Gastroenterology"
        assert "PAT-Gastro-007" in data["referral_letter_text"]
