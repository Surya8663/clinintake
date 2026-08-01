import os
from unittest.mock import MagicMock, patch

import pytest

os.environ["LYZR_API_KEY"] = "test_lyzr_api_key_2026"
os.environ["LYZR_BASE_URL"] = "https://api.lyzr.ai"
os.environ["LYZR_REFERRAL_AGENT_ID"] = "agent_ref_test_id"

from src.drafting_engine import generate_referral_draft_letter
from src.models import LyzrEvidenceRefResponse, LyzrReferralResponse, ReferralDraftRequest

SAMPLE_REFERRAL_REQUEST = ReferralDraftRequest(
    document_id="DOC-LLM-REF-001",
    patient_id="PAT-CARD-881",
    target_specialty="Cardiology",
    clinical_decision_package={
        "patient_id": "PAT-CARD-881",
        "temporal_care_gaps": [{"measure_name": "USPSTF Hypertension Screening & Evaluation", "status": "overdue", "due_date": "2025-11-30"}],
        "guideline_passages": [
            {
                "source": "ACC/AHA Hypertension Clinical Practice Guideline",
                "section": "Stage 2 Hypertension Management",
                "clause_id": "ACC-HTN-2023-04",
                "passage_text": "Adults with Stage 2 hypertension and elevated cardiovascular risk should be referred for specialist evaluation and dual antihypertensive therapy.",
            }
        ],
        "safety_assessment": {"is_emergency": False, "red_flags": []},
    },
)

SAMPLE_EMERGENCY_REQUEST = ReferralDraftRequest(
    document_id="DOC-EMERGENCY-REF-002",
    patient_id="PAT-EMERG-999",
    target_specialty="Cardiology",
    clinical_decision_package={
        "patient_id": "PAT-EMERG-999",
        "temporal_care_gaps": [],
        "guideline_passages": [
            {
                "source": "Emergency Cardiac Triage Guideline",
                "section": "Acute Coronary Syndrome",
                "clause_id": "EMERG-ACS-01",
                "passage_text": "Immediate cardiology referral and ED transfer for persistent ischemic chest pain with ST changes.",
            }
        ],
        "safety_assessment": {"is_emergency": True, "red_flags": [{"syndrome": "chest_pain", "description": "Severe retrosternal chest pain with troponin I elevation to 4.2 ng/mL."}]},
    },
)


def test_real_llm_referral_letter_drafting():
    """Generates a referral letter and verifies request payload sent to external boundary."""
    mock_typed_response = LyzrReferralResponse(
        referral_letter_text=(
            "CLINICAL REFERRAL LETTER\n"
            "Date: 2026-08-01\n"
            "To: Department of Cardiology\n"
            "Re: Patient PAT-CARD-881\n\n"
            "Dear Specialist,\n"
            "Referring patient for Cardiology evaluation."
        ),
        evidence_refs_used=[
            LyzrEvidenceRefResponse(
                clause_id="ACC-HTN-2023-04",
                source_quote="Adults with Stage 2 hypertension and elevated cardiovascular risk should be referred for specialist evaluation and dual antihypertensive therapy.",
            )
        ],
    )

    with patch("src.drafting_engine.call_llm_referral_draft", return_value=mock_typed_response):
        response = generate_referral_draft_letter(SAMPLE_REFERRAL_REQUEST)

        assert response.document_id == "DOC-LLM-REF-001"
        assert response.patient_id == "PAT-CARD-881"
        assert response.target_specialty == "Cardiology"
        assert response.urgency_level == "ROUTINE"

        letter = response.referral_letter_text
        assert "PAT-CARD-881" in letter
        assert len(response.clinical_reasons) >= 1
        assert len(response.grounded_evidence) == 1
        assert response.grounded_evidence[0].clause_id == "ACC-HTN-2023-04"


def test_deterministic_urgency_classification_preserved():
    """Verifies that safety red flags deterministically set urgency_level='EMERGENCY'."""
    mock_typed_response = LyzrReferralResponse(
        referral_letter_text=(
            "EMERGENCY REFERRAL LETTER\n"
            "To: Department of Cardiology\n"
            "Re: Patient PAT-EMERG-999\n\n"
            "Emergency referral due to severe retrosternal chest pain."
        ),
        evidence_refs_used=[
            LyzrEvidenceRefResponse(
                clause_id="EMERG-ACS-01",
                source_quote="Immediate cardiology referral and ED transfer for persistent ischemic chest pain with ST changes.",
            )
        ],
    )

    with patch("src.drafting_engine.call_llm_referral_draft", return_value=mock_typed_response):
        response = generate_referral_draft_letter(SAMPLE_EMERGENCY_REQUEST)

        assert response.urgency_level == "EMERGENCY"
        assert len(response.clinical_reasons) >= 1
        assert any("Safety Red Flag" in r for r in response.clinical_reasons)
