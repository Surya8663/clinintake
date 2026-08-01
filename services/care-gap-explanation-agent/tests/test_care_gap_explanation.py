import os
from unittest.mock import patch

from fastapi.testclient import TestClient
import pytest

os.environ["LYZR_API_KEY"] = "test_lyzr_api_key_2026"
os.environ["LLM_API_KEY"] = "test_llm_api_key_2026"

from src.main import app

client = TestClient(app)


def test_care_gap_agent_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_explanation_generation_from_package():
    package_data = {
        "document_id": "DOC-PKG-001",
        "patient_id": "PAT-100",
        "temporal_care_gaps": [{"measure_name": "USPSTF Colorectal Cancer Screening", "status": "overdue", "due_date": "2025-06-15"}],
        "guideline_passages": [
            {
                "source": "USPSTF Colorectal Screening Recommendation Summary 2021",
                "version": "2021",
                "section": "Recommendation Statement",
                "clause_id": "USPSTF-CRC-2021-01",
                "passage_text": "The USPSTF recommends screening for colorectal cancer in all adults aged 45 to 75 years.",
                "similarity_score": 0.89,
            }
        ],
        "safety_assessment": {"is_emergency": False},
    }

    mock_llm_res = {
        "explanation_summary": "USPSTF Colorectal Cancer Screening is currently OVERDUE for adult patient.",
        "citations_used": [{"source_title": "USPSTF Colorectal Screening Recommendation Summary 2021", "clause_id": "USPSTF-CRC-2021-01"}],
    }

    with patch("src.llm_client.call_llm_explanation", return_value=mock_llm_res):
        response = client.post("/care-gap/explain", json=package_data)
        assert response.status_code == 200
        data = response.json()
        assert data["document_id"] == "DOC-PKG-001"
        assert "USPSTF Colorectal Cancer Screening is currently OVERDUE" in data["explanation_summary"]
        assert len(data["cited_guideline_passages"]) == 1

        citation = data["cited_guideline_passages"][0]
        assert citation["clause_id"] == "USPSTF-CRC-2021-01"
        assert citation["section"] == "Recommendation Statement"
        assert "adults aged 45 to 75 years" in citation["passage_text"]


def test_citations_strictly_match_input_package_passages_not_fabricated():
    unique_clause_id = "USPSTF-DIABETES-2021-CLAUSE-99"
    unique_passage_text = "Screening for prediabetes and type 2 diabetes should occur in asymptomatic adults aged 35 to 70 years who have overweight or obesity."

    package_data = {
        "document_id": "DOC-STRICT-CITATION-02",
        "guideline_passages": [
            {
                "source": "USPSTF Diabetes Screening 2021",
                "version": "2021",
                "section": "Target Population",
                "clause_id": unique_clause_id,
                "passage_text": unique_passage_text,
                "similarity_score": 0.95,
            }
        ],
    }

    mock_llm_res = {
        "explanation_summary": "Screening for diabetes recommended.",
        "citations_used": [{"source_title": "USPSTF Diabetes Screening 2021", "clause_id": unique_clause_id}],
    }

    with patch("src.llm_client.call_llm_explanation", return_value=mock_llm_res):
        response = client.post("/care-gap/explain", json=package_data)
        assert response.status_code == 200
        data = response.json()

        cited_passages = data["cited_guideline_passages"]
        assert len(cited_passages) == 1
        assert cited_passages[0]["clause_id"] == unique_clause_id
        assert cited_passages[0]["passage_text"] == unique_passage_text


def test_empty_guideline_evidence_returns_insufficient_evidence():
    """Test F9: Empty guideline evidence returns 'Insufficient guideline evidence'."""
    package_data = {
        "document_id": "DOC-EMPTY-GUIDELINE-01",
        "patient_id": "PAT-200",
        "temporal_care_gaps": [],
        "guideline_passages": [],
        "safety_assessment": {"is_emergency": False},
    }

    response = client.post("/care-gap/explain", json=package_data)
    assert response.status_code == 200
    data = response.json()
    assert data["explanation_summary"] == "Insufficient guideline evidence"
