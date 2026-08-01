from fastapi.testclient import TestClient

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

    response = client.post("/referral/draft", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["document_id"] == "DOC-REF-001"
    assert data["target_specialty"] == "Gastroenterology"
    assert len(data["referral_letter_text"]) > 50
    assert "PAT-Gastro-007" in data["referral_letter_text"]
    assert "Gastroenterology" in data["referral_letter_text"]
    assert "Colorectal" in data["referral_letter_text"] or "colorectal" in data["referral_letter_text"].lower()
    assert len(data["grounded_evidence"]) == 1
    assert data["grounded_evidence"][0]["clause_id"] == "CRC-2021-01"
