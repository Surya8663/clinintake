from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)

def test_interaction_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_drug_drug_interaction_detection():
    response = client.post(
        "/interactions/check",
        json={
            "medications": [
                {"name": "Lisinopril 10mg", "rxnorm_code": "314076"},
                {"name": "Potassium Chloride 20mEq", "rxnorm_code": "855324"}
            ],
            "allergies": []
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["has_interactions"] is True
    assert data["has_high_severity"] is True
    assert len(data["interactions"]) >= 1
    
    inter = data["interactions"][0]
    assert inter["interaction_type"] == "drug-drug"
    assert inter["severity"] == "high"

def test_drug_allergy_interaction_detection():
    response = client.post(
        "/interactions/check",
        json={
            "medications": [
                {"name": "Lisinopril 10mg", "rxnorm_code": "314076"}
            ],
            "allergies": [
                {"substance": "ACE Inhibitors", "reaction": "Angioedema"}
            ]
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["has_interactions"] is True
    assert data["has_high_severity"] is True
    assert len(data["interactions"]) >= 1
    
    inter = data["interactions"][0]
    assert inter["interaction_type"] == "drug-allergy"
    assert inter["severity"] == "high"
