from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_fhir_integration_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["ehr_client_configured"] is True

def test_fhir_transaction_write_persistence():
    payload = {
        "document_id": "DOC-FHIR-100",
        "patient_id": "PAT-99882",
        "idempotency_key": "IDEM-KEY-UNIQUE-001",
        "fhir_resources": [
            {
                "resourceType": "Patient",
                "id": "PAT-99882",
                "name": [{"family": "Smith", "given": ["John"]}]
            },
            {
                "resourceType": "Observation",
                "status": "final",
                "code": {"text": "USPSTF Colorectal Cancer Screening Status"}
            }
        ]
    }

    response = client.post("/fhir/write-transaction", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "persisted"
    assert data["is_duplicate"] is False
    assert len(data["resource_references"]) >= 2

def test_idempotency_deduplication_suppresses_duplicate_transaction_as_no_op():
    """
    CRITICAL PRD 5.8 REQUIREMENT TEST:
    Proves that submitting the identical transaction twice with the same idempotency key
    results in the second request being recognized as a duplicate and returned as a no-op,
    preventing duplicate record creation in the EHR.
    """
    same_idempotency_key = "IDEM-KEY-DUPLICATE-TEST-77"
    payload = {
        "document_id": "DOC-FHIR-DUP-01",
        "patient_id": "PAT-DUP-101",
        "idempotency_key": same_idempotency_key,
        "fhir_resources": [
            {
                "resourceType": "Condition",
                "code": {"text": "Type 2 Diabetes Mellitus"}
            }
        ]
    }

    # 1. First execution -> Must persist
    resp1 = client.post("/fhir/write-transaction", json=payload)
    assert resp1.status_code == 200
    data1 = resp1.json()
    assert data1["status"] == "persisted"
    assert data1["is_duplicate"] is False
    bundle_id_1 = data1["fhir_bundle_id"]

    # 2. Second execution (same idempotency key) -> MUST be suppressed as duplicate no-op
    resp2 = client.post("/fhir/write-transaction", json=payload)
    assert resp2.status_code == 200
    data2 = resp2.json()
    
    assert data2["is_duplicate"] is True
    assert data2["fhir_bundle_id"] == bundle_id_1 # Same bundle ID returned
