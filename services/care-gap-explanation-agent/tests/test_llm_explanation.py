import os
from unittest.mock import patch

import pytest

os.environ["LYZR_API_KEY"] = "test_lyzr_api_key_2026"
os.environ["LLM_API_KEY"] = "test_llm_api_key_2026"

from src.explanation_engine import (
    GroundingVerificationError,
    _get_valid_citation_keys,
    _verify_citations,
    generate_care_gap_explanation,
)
from src.models import ClinicalDecisionPackage

SAMPLE_PACKAGE = ClinicalDecisionPackage(
    document_id="DOC-LLM-TEST-001",
    patient_id="PAT-55021",
    temporal_care_gaps=[
        {"measure_name": "USPSTF Colorectal Cancer Screening", "status": "overdue", "due_date": "2025-06-15"},
        {"measure_name": "USPSTF Diabetes Screening", "status": "due", "due_date": "2026-01-01"},
    ],
    guideline_passages=[
        {
            "source": "USPSTF Colorectal Screening Recommendation 2021",
            "version": "2021",
            "section": "Recommendation Statement",
            "clause_id": "USPSTF-CRC-2021-A",
            "passage_text": "The USPSTF recommends screening for colorectal cancer in all adults aged 45 to 75 years.",
            "similarity_score": 0.91,
        },
        {
            "source": "USPSTF Prediabetes and Type 2 Diabetes Screening 2021",
            "version": "2021",
            "section": "Target Population",
            "clause_id": "USPSTF-DM-2021-B",
            "passage_text": "Screening for prediabetes and type 2 diabetes in asymptomatic adults aged 35 to 70 years who have overweight or obesity.",
            "similarity_score": 0.87,
        },
    ],
    safety_assessment={"is_emergency": False},
    drug_interactions=[],
)


def test_successful_llm_generated_explanation():
    """Test 1: Normal successful LLM-generated explanation."""
    mock_llm_res = {
        "explanation_summary": "Screening for colorectal cancer and diabetes is indicated based on USPSTF guidelines.",
        "citations_used": [
            {"source_title": "USPSTF Colorectal Screening Recommendation 2021", "clause_id": "USPSTF-CRC-2021-A"},
            {"source_title": "USPSTF Prediabetes and Type 2 Diabetes Screening 2021", "clause_id": "USPSTF-DM-2021-B"},
        ],
    }

    with patch("src.llm_client.call_llm_explanation", return_value=mock_llm_res):
        result = generate_care_gap_explanation(SAMPLE_PACKAGE)

        assert result.generation_mode == "llm"
        assert len(result.explanation_summary) > 20
        assert len(result.care_gaps_found) == 2
        assert len(result.cited_guideline_passages) == 2
        clause_ids = {c.clause_id for c in result.cited_guideline_passages}
        assert "USPSTF-CRC-2021-A" in clause_ids
        assert "USPSTF-DM-2021-B" in clause_ids


def test_citation_verification_catches_invalid_citations():
    """Test 2: Proves citation verification function flags unsupported citations."""
    fake_llm_result = {
        "explanation_summary": "Some explanation referencing a fake guideline.",
        "citations_used": [
            {"source_title": "USPSTF Colorectal Screening Recommendation 2021", "clause_id": "USPSTF-CRC-2021-A"},
            {"source_title": "FABRICATED Guideline That Does Not Exist", "clause_id": "FAKE-CLAUSE-999"},
        ],
    }
    valid_keys = _get_valid_citation_keys(SAMPLE_PACKAGE)
    violations = _verify_citations(fake_llm_result, valid_keys)

    assert len(violations) >= 1
    assert any("FABRICATED" in v or "FAKE-CLAUSE-999" in v for v in violations)


def test_explanation_with_nonexistent_citation_rejected():
    """Test F8: Explanation with a nonexistent citation is rejected after retry."""
    fabricated_response = {
        "explanation_summary": "Explanation with invented citation.",
        "citations_used": [{"source_title": "INVENTED GUIDELINE NOT IN PACKAGE", "clause_id": "INVENTED-CLAUSE-000"}],
    }

    with patch("src.llm_client.call_llm_explanation", return_value=fabricated_response):
        with pytest.raises(GroundingVerificationError):
            generate_care_gap_explanation(SAMPLE_PACKAGE)
