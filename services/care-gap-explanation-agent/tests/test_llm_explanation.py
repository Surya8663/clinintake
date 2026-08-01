from unittest.mock import MagicMock, patch

import pytest

from src.explanation_engine import GroundingVerificationError, generate_care_gap_explanation
from src.models import CitationItem, ClinicalDecisionPackage, LyzrCitationResponse, LyzrExplanationResponse


def test_explanation_with_care_gaps_and_guideline_evidence_and_zero_citations_rejected():
    """Condition 10: Explanation discussing care gaps supported by guideline evidence with zero citations is rejected."""
    package = ClinicalDecisionPackage(
        document_id="DOC-ZERO-CITE",
        patient_id="PAT-ZERO-01",
        temporal_care_gaps=[{"measure_name": "Colorectal Cancer Screening", "status": "overdue"}],
        guideline_passages=[
            {
                "source_title": "USPSTF CRC 2021",
                "version": "2021",
                "section": "Recommendation",
                "clause_id": "USPSTF-CRC-2021-01",
                "passage_text": "Screening for colorectal cancer in adults aged 45-75.",
            }
        ],
    )

    # LLM returns explanation with zero citations
    mock_zero_cite_response = LyzrExplanationResponse(
        explanation_summary="Patient is overdue for colorectal screening.",
        citations_used=[],  # Zero citations
    )

    with patch("src.llm_client.call_llm_explanation", return_value=mock_zero_cite_response):
        with pytest.raises(GroundingVerificationError) as exc_info:
            generate_care_gap_explanation(package)

        assert "zero cited guideline passages" in str(exc_info.value)


def test_missing_similarity_score_is_not_replaced_with_1_0():
    """Condition 11: Missing similarity_score in retrieved passage is preserved as None, not assigned 1.0."""
    package = ClinicalDecisionPackage(
        document_id="DOC-NO-SIMSCORE",
        patient_id="PAT-SIM-01",
        temporal_care_gaps=[{"measure_name": "Colorectal Cancer Screening", "status": "overdue"}],
        guideline_passages=[
            {
                "source_title": "USPSTF CRC 2021",
                "version": "2021",
                "section": "Recommendation",
                "clause_id": "USPSTF-CRC-2021-01",
                "passage_text": "Screening for colorectal cancer in adults aged 45-75.",
                # similarity_score omitted
            }
        ],
    )

    mock_valid_response = LyzrExplanationResponse(
        explanation_summary="Patient is overdue for colorectal screening per USPSTF guidelines.",
        citations_used=[
            LyzrCitationResponse(source_title="USPSTF CRC 2021", clause_id="USPSTF-CRC-2021-01")
        ],
    )

    with patch("src.llm_client.call_llm_explanation", return_value=mock_valid_response):
        response = generate_care_gap_explanation(package)
        assert len(response.cited_guideline_passages) == 1
        assert response.cited_guideline_passages[0].similarity_score is None
        assert response.cited_guideline_passages[0].similarity_score != 1.0


def test_source_from_one_guideline_plus_clause_from_another_rejected():
    package = ClinicalDecisionPackage(
        document_id="DOC-MIXED-CITE",
        patient_id="PAT-MIXED-01",
        temporal_care_gaps=[{"measure_name": "Colorectal Cancer Screening", "status": "overdue"}],
        guideline_passages=[
            {
                "source_title": "USPSTF CRC 2021",
                "version": "2021",
                "section": "Recommendation",
                "clause_id": "USPSTF-CRC-2021-01",
                "passage_text": "Screening for colorectal cancer in adults aged 45-75.",
            },
            {
                "source_title": "ADA Diabetes 2024",
                "version": "2024",
                "section": "Monitoring",
                "clause_id": "ADA-2024-HBA1C-01",
                "passage_text": "HbA1c testing twice yearly.",
            },
        ],
    )

    mock_mixed_response = LyzrExplanationResponse(
        explanation_summary="Patient is overdue for colorectal screening.",
        citations_used=[
            LyzrCitationResponse(source_title="ADA Diabetes 2024", clause_id="USPSTF-CRC-2021-01")
        ],
    )

    with patch("src.llm_client.call_llm_explanation", return_value=mock_mixed_response):
        with pytest.raises(GroundingVerificationError) as exc_info:
            generate_care_gap_explanation(package)

        assert "does not exist together in any single supplied guideline passage" in str(exc_info.value)
