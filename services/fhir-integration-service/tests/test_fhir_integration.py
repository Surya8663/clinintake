import hashlib
import hmac
import json
import os
import time

from fastapi.testclient import TestClient

os.environ["EHR_CLIENT_SECRET"] = "test_ehr_secret_2026"
os.environ["EHR_API_KEY"] = "test_ehr_api_key_2026"
os.environ["JWT_SECRET_KEY"] = "test_fhir_jwt_secret_2026"

from services.common.jwt_verifier import _b64_encode
from src.main import app

client = TestClient(app)


def get_m2m_auth_header():
    now = int(time.time())
    exp = now + 3600
    scopes = ["service:internal"]
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": "service:clinintake-m2m",
        "client_id": "clinintake-m2m",
        "azp": "clinintake-m2m",
        "role": "CLINICAL_AGENT",
        "roles": scopes,
        "realm_access": {"roles": scopes},
        "scopes": scopes,
        "iss": "http://localhost:8085/realms/clinintake",
        "aud": "clinintake-backend-services",
        "iat": now,
        "exp": exp,
    }
    header_b64 = _b64_encode(json.dumps(header).encode("utf-8"))
    payload_b64 = _b64_encode(json.dumps(payload).encode("utf-8"))
    message = f"{header_b64}.{payload_b64}"
    sig = hmac.new(b"test_fhir_jwt_secret_2026", message.encode("utf-8"), hashlib.sha256).digest()
    token = f"{message}.{_b64_encode(sig)}"
    return {"Authorization": f"Bearer {token}"}


def test_fhir_integration_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["ehr_client_configured"] is True


def test_fhir_transaction_write_persistence():
    headers = get_m2m_auth_header()
    payload = {
        "document_id": "DOC-FHIR-100",
        "patient_id": "PAT-99882",
        "idempotency_key": "IDEM-KEY-UNIQUE-001",
        "fhir_resources": [
            {"resourceType": "Patient", "id": "PAT-99882", "name": [{"family": "Smith", "given": ["John"]}]},
            {"resourceType": "Observation", "status": "final", "code": {"text": "USPSTF Colorectal Cancer Screening Status"}},
        ],
    }

    response = client.post("/fhir/write-transaction", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "persisted"
    assert data["is_duplicate"] is False
    assert len(data["resource_references"]) >= 2


def test_idempotency_deduplication_suppresses_duplicate_transaction_as_no_op():
    headers = get_m2m_auth_header()
    same_idempotency_key = "IDEM-KEY-DUPLICATE-TEST-77"
    payload = {
        "document_id": "DOC-FHIR-DUP-01",
        "patient_id": "PAT-DUP-101",
        "idempotency_key": same_idempotency_key,
        "fhir_resources": [{"resourceType": "Condition", "code": {"text": "Type 2 Diabetes Mellitus"}}],
    }

    # 1. First execution -> Must persist
    resp1 = client.post("/fhir/write-transaction", json=payload, headers=headers)
    assert resp1.status_code == 200
    data1 = resp1.json()
    assert data1["status"] == "persisted"
    assert data1["is_duplicate"] is False
    bundle_id_1 = data1["fhir_bundle_id"]

    # 2. Second execution (same idempotency key) -> MUST be suppressed as duplicate no-op
    resp2 = client.post("/fhir/write-transaction", json=payload, headers=headers)
    assert resp2.status_code == 200
    data2 = resp2.json()

    assert data2["is_duplicate"] is True
    assert data2["fhir_bundle_id"] == bundle_id_1

def test_missing_auth_header_fails():
    payload = {
        "document_id": "DOC-NOAUTH",
        "patient_id": "PAT-NOAUTH",
        "idempotency_key": "IDEM-NOAUTH",
        "fhir_resources": []
    }
    response = client.post("/fhir/write-transaction", json=payload)
    assert response.status_code == 401

def test_invalid_auth_header_fails():
    payload = {
        "document_id": "DOC-BADAUTH",
        "patient_id": "PAT-BADAUTH",
        "idempotency_key": "IDEM-BADAUTH",
        "fhir_resources": []
    }
    response = client.post("/fhir/write-transaction", json=payload, headers={"Authorization": "Bearer bad_token"})
    assert response.status_code == 401
