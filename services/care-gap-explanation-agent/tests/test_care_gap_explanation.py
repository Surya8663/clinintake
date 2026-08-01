from fastapi.testclient import TestClient

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
        "temporal_care_gaps": [
            {
                "measure_name": "USPSTF Colorectal Cancer Screening",
                "status": "overdue",
                "due_date": "2025-06-15"
            }
        ],
        "guideline_passages": [
            {
                "source": "USPSTF Colorectal Screening Recommendation Summary 2021",
                "version": "2021",
                "section": "Recommendation Statement",
                "clause_id": "USPSTF-CRC-2021-01",
                "passage_text": "The USPSTF recommends screening for colorectal cancer in all adults aged 45 to 75 years.",
                "similarity_score": 0.89
            }
        ],
        "safety_assessment": {
            "is_emergency": False
        }
    }

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
    """
    CRITICAL PRD 5.4 / 5.5 REQUIREMENT TEST:
    Proves that the Care-Gap Explanation Agent output references REAL citation data
    present in the input ClinicalDecisionPackage, and contains NO fabricated citations.
    """
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
                "similarity_score": 0.95
            }
        ]
    }

    response = client.post("/care-gap/explain", json=package_data)
    assert response.status_code == 200
    data = response.json()

    cited_passages = data["cited_guideline_passages"]
    assert len(cited_passages) == 1

    # Verify exact match against input package
    assert cited_passages[0]["clause_id"] == unique_clause_id
    assert cited_passages[0]["passage_text"] == unique_passage_text

    # Confirm no extra or fabricated citations were generated
    for citation in cited_passages:
        assert citation["clause_id"] in [p["clause_id"] for p in package_data["guideline_passages"]]
