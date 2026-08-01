from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)


def test_cql_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_cql_evaluation_diabetes_inclusion():
    clinical_data = {
        "diagnoses": [{"name": {"value": "Essential Hypertension"}, "icd10_code": {"value": "I10"}}],
        "medications": [{"name": {"value": "Lisinopril 10mg"}, "rxnorm_code": {"value": "314076"}}],
        "labs": [{"name": {"value": "HbA1c"}, "loinc_code": {"value": "4548-4"}, "value": {"value": "7.2 %"}}],
    }

    response = client.post("/cql/evaluate", json={"patient_id": "PAT-7710", "clinical_data": clinical_data, "rule_library": ["Diabetes_Screening", "Hypertension_Control"]})
    assert response.status_code == 200
    data = response.json()
    assert data["is_eligible"] is True
    assert "Diabetes_Care_Management_Protocol" in data["inclusion_criteria_met"]
    assert "Hypertension_Control_Protocol" in data["inclusion_criteria_met"]
    assert len(data["exclusion_criteria_met"]) == 0
