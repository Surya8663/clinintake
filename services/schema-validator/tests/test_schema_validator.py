from fastapi.testclient import TestClient

from src.main import app
from src.validator_engine import validate_fhir_resource_schema

client = TestClient(app)


def test_validator_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_valid_fhir_condition_resource():
    valid_condition = {
        "resourceType": "Condition",
        "id": "cond-101",
        "clinicalStatus": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-clinical", "code": "active"}]},
        "verificationStatus": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-ver-status", "code": "confirmed"}]},
        "code": {"coding": [{"system": "http://snomed.info/sct", "code": "59621000", "display": "Essential Hypertension"}]},
        "subject": {"reference": "Patient/PAT-001"},
    }

    response = client.post("/validate/schema", json={"resource_type": "Condition", "fhir_resource": valid_condition})
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid"] is True
    assert len(data["issues"]) == 0


def test_deliberately_invalid_fhir_resource_rejected():
    """
    CRITICAL PRD REQUIREMENT TEST:
    Proves that a deliberately malformed FHIR resource is rejected (HTTP 422),
    returning is_valid=False and explicit field-level error messages.
    """
    # Malformed MedicationStatement: Missing required 'medication' field
    invalid_med_statement = {
        "resourceType": "MedicationStatement",
        "id": "med-invalid-99",
        "status": "recorded",
        # Missing 'medication' required field!
        "subject": {"reference": "Patient/PAT-001"},
    }

    response = client.post("/validate/schema", json={"resource_type": "MedicationStatement", "fhir_resource": invalid_med_statement})

    # Must be rejected with HTTP 422 Unprocessable Entity
    assert response.status_code == 422
    data = response.json()
    assert data["is_valid"] is False
    assert len(data["issues"]) > 0

    # Verify specific error detail for the missing 'medication' field
    issue = data["issues"][0]
    assert "medication" in issue["field"]
    assert issue["issue_type"] == "missing_required"
    assert issue["severity"] == "error"
