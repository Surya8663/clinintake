from unittest.mock import patch

import pytest

from src.explanation_engine import GroundingVerificationError, generate_care_gap_explanation
from src.models import ClinicalDecisionPackage


def test_source_from_one_guideline_plus_clause_from_another_rejected():
    """Condition 10: Mixing source_title from passage A with clause_id from passage B raises GroundingVerificationError."""
    package = ClinicalDecisionPackage(
        document_id="DOC-MIXED-CITE",
        patient_id="PAT-MIXED-01",
        temporal_care_gaps=[{"measure_name": "Colorectal Cancer Screening", "status": "overdue"}],
        guideline_passages=[
            {
                "source": "USPSTF CRC 2021",
                "source_title": "USPSTF CRC 2021",
                "version": "2021",
                "section": "Recommendation",
                "clause_id": "USPSTF-CRC-2021-01",
                "passage_text": "Screening for colorectal cancer in adults aged 45-75.",
            },
            {
                "source": "ADA Diabetes 2024",
                "source_title": "ADA Diabetes 2024",
                "version": "2024",
                "section": "Monitoring",
                "clause_id": "ADA-2024-HBA1C-01",
                "passage_text": "HbA1c testing twice yearly.",
            },
        ],
    )

    # LLM mixes source_title from ADA with clause_id from USPSTF
    mock_mixed_llm_result = {
        "explanation_summary": "Patient is overdue for colorectal screening according to guidelines.",
        "citations_used": [
            {
                "source_title": "ADA Diabetes 2024",  # Source from Passage 2
                "clause_id": "USPSTF-CRC-2021-01",  # Clause from Passage 1
            }
        ],
    }

    with patch("src.llm_client.call_llm_explanation", return_value=mock_mixed_llm_result):
        with pytest.raises(GroundingVerificationError) as exc_info:
            generate_care_gap_explanation(package)

        assert "does not exist together in any single supplied guideline passage" in str(exc_info.value)
