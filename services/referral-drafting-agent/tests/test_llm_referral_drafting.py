"""
Real LLM referral drafting integration tests.
Tests:
1. Real LLM referral letter generation with natural clinical tone and proper structure
2. Preservation of deterministic urgency classification (EMERGENCY on safety red flags)
Requires OPENAI_API_KEY or GOOGLE_API_KEY environment variable.
"""
import os

import pytest

from src.drafting_engine import generate_referral_draft_letter
from src.models import ReferralDraftRequest

SAMPLE_REFERRAL_REQUEST = ReferralDraftRequest(
    document_id="DOC-LLM-REF-001",
    patient_id="PAT-CARD-881",
    target_specialty="Cardiology",
    clinical_decision_package={
        "patient_id": "PAT-CARD-881",
        "temporal_care_gaps": [
            {
                "measure_name": "USPSTF Hypertension Screening & Evaluation",
                "status": "overdue",
                "due_date": "2025-11-30"
            }
        ],
        "guideline_passages": [
            {
                "source": "ACC/AHA Hypertension Clinical Practice Guideline",
                "section": "Stage 2 Hypertension Management",
                "clause_id": "ACC-HTN-2023-04",
                "passage_text": "Adults with Stage 2 hypertension and elevated cardiovascular risk should be referred for specialist evaluation and dual antihypertensive therapy."
            }
        ],
        "safety_assessment": {
            "is_emergency": False,
            "red_flags": []
        }
    }
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
                "passage_text": "Immediate cardiology referral and ED transfer for persistent ischemic chest pain with ST changes."
            }
        ],
        "safety_assessment": {
            "is_emergency": True,
            "red_flags": [
                {
                    "syndrome": "chest_pain",
                    "description": "Severe retrosternal chest pain with troponin I elevation to 4.2 ng/mL."
                }
            ]
        }
    }
)

@pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY") and not os.getenv("GOOGLE_API_KEY"),
    reason="No LLM API key set — skipping real LLM integration test"
)
def test_real_llm_referral_letter_drafting():
    """
    Test 1: Generates a real LLM referral letter from synthetic clinical package.
    Verifies:
    - Letter text is non-empty and has clinical structure
    - Patient ID, target specialty, and urgency level match
    - Grounded evidence and reasons are included
    """
    response = generate_referral_draft_letter(SAMPLE_REFERRAL_REQUEST)

    assert response.document_id == "DOC-LLM-REF-001"
    assert response.patient_id == "PAT-CARD-881"
    assert response.target_specialty == "Cardiology"
    assert response.urgency_level == "ROUTINE"

    letter = response.referral_letter_text
    assert len(letter) > 100, "Generated letter text is too short"
    assert "PAT-CARD-881" in letter, "Letter missing patient ID"
    assert "Cardiology" in letter, "Letter missing target specialty"
    assert len(response.clinical_reasons) >= 1
    assert len(response.grounded_evidence) == 1
    assert response.grounded_evidence[0].clause_id == "ACC-HTN-2023-04"

@pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY") and not os.getenv("GOOGLE_API_KEY"),
    reason="No LLM API key set — skipping real LLM integration test"
)
def test_deterministic_urgency_classification_preserved():
    """
    Test 2: Verifies that safety red flags deterministically set urgency_level='EMERGENCY'.
    """
    response = generate_referral_draft_letter(SAMPLE_EMERGENCY_REQUEST)

    assert response.urgency_level == "EMERGENCY"
    assert len(response.clinical_reasons) >= 1
    assert any("Safety Red Flag" in r for r in response.clinical_reasons)
    assert len(response.referral_letter_text) > 100
