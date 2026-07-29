import os
import sys
import pytest
import importlib.util
from pathlib import Path

os.environ["EHR_CLIENT_SECRET"] = "test_ehr_secret_2026"
os.environ["EHR_API_KEY"] = "test_ehr_api_key_2026"
os.environ["HMAC_SECRET_KEY"] = "test_hmac_secret_2026"
os.environ["JWT_SECRET_KEY"] = "test_authorization_matrix_secret_key_2026"
os.environ["KEYCLOAK_CLIENT_SECRET"] = "test_keycloak_client_secret_2026"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"

from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

def load_app_from_service(service_name: str):
    for k in list(sys.modules.keys()):
        if k == 'src' or k.startswith('src.'):
            del sys.modules[k]

    service_dir = REPO_ROOT / "services" / service_name
    service_path = service_dir / "src" / "main.py"
    
    sys.path.insert(0, str(service_dir))
    spec = importlib.util.spec_from_file_location(f"{service_name.replace('-', '_')}.main", service_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    sys.path.pop(0)
    return module.app

iam_app = load_app_from_service("iam-service")
workspace_app = load_app_from_service("clinical-workspace")
compliance_app = load_app_from_service("compliance-dashboard")
metrics_app = load_app_from_service("metrics-dashboard")
fhir_app = load_app_from_service("fhir-integration-service")

iam_client = TestClient(iam_app)
workspace_client = TestClient(workspace_app)
compliance_client = TestClient(compliance_app)
metrics_client = TestClient(metrics_app)
fhir_client = TestClient(fhir_app)

def get_token_for(username: str, role: str, scopes: list) -> str:
    from services.common.jwt_verifier import _b64_encode
    import time, json, hmac, hashlib
    now = int(time.time())
    exp = now + 900
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": username,
        "preferred_username": username,
        "role": role,
        "roles": scopes,
        "realm_access": {"roles": scopes},
        "scopes": scopes,
        "scope": " ".join(scopes),
        "iss": "http://localhost:8085/realms/clinintake",
        "aud": "clinintake-bff",
        "iat": now,
        "exp": exp
    }
    header_b64 = _b64_encode(json.dumps(header).encode('utf-8'))
    payload_b64 = _b64_encode(json.dumps(payload).encode('utf-8'))
    message = f"{header_b64}.{payload_b64}"
    sig = hmac.new(b"test_authorization_matrix_secret_key_2026", message.encode('utf-8'), hashlib.sha256).digest()
    return f"{message}.{_b64_encode(sig)}"

def get_m2m_token() -> str:
    from services.common.jwt_verifier import _b64_encode
    import time, json, hmac, hashlib
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
        "exp": exp
    }
    header_b64 = _b64_encode(json.dumps(header).encode('utf-8'))
    payload_b64 = _b64_encode(json.dumps(payload).encode('utf-8'))
    message = f"{header_b64}.{payload_b64}"
    sig = hmac.new(b"test_authorization_matrix_secret_key_2026", message.encode('utf-8'), hashlib.sha256).digest()
    return f"{message}.{_b64_encode(sig)}"

# 1. Missing Authorization Token -> 401
def test_missing_token_returns_401():
    res = workspace_client.get("/workspace/reviews")
    assert res.status_code == 401
    assert "Missing authorization token" in res.json()["detail"]

# 2. Invalid Token Signature -> 401
def test_invalid_signature_returns_401():
    headers = {"Authorization": "Bearer invalid.jwt.token.signature"}
    res = workspace_client.get("/workspace/reviews", headers=headers)
    assert res.status_code == 401

# 3. Insufficient Role -> 403 Forbidden
def test_compliance_user_cannot_approve_clinical_decision():
    auditor_token = get_token_for("auditor_jane", "COMPLIANCE_REVIEWER", ["compliance:audit:read"])
    headers = {"Authorization": f"Bearer {auditor_token}"}
    payload = {
        "decision": "APPROVED",
        "digital_signature": "SIG-HMAC256-TEST"
    }
    res = workspace_client.post("/workspace/decision/DOC-99482-A", json=payload, headers=headers)
    assert res.status_code == 403
    assert "Insufficient privileges" in res.json()["detail"]

# 4. Clinician can review and approve clinical decision
def test_clinician_can_approve_clinical_decision():
    clinician_token = get_token_for("dr_smith", "TREATING_CLINICIAN", ["clinician:review", "clinician:approve", "clinician:reject"])
    headers = {"Authorization": f"Bearer {clinician_token}"}
    payload = {
        "decision": "APPROVED",
        "digital_signature": "SIG-HMAC256-TEST"
    }
    res = workspace_client.post("/workspace/decision/DOC-99482-A", json=payload, headers=headers)
    assert res.status_code == 200
    assert res.json()["status"] == "approved"

# 5. Clinician cannot access compliance audit trail (Role segregation)
def test_clinician_cannot_access_compliance_audit_trail():
    clinician_token = get_token_for("dr_smith", "TREATING_CLINICIAN", ["clinician:review", "clinician:approve"])
    headers = {"Authorization": f"Bearer {clinician_token}"}
    res = compliance_client.get("/compliance/audit-trail", headers=headers)
    assert res.status_code == 403

# 6. Compliance reviewer can access compliance audit trail
def test_compliance_user_can_access_compliance_audit_trail():
    auditor_token = get_token_for("auditor_jane", "COMPLIANCE_REVIEWER", ["compliance:audit:read"])
    headers = {"Authorization": f"Bearer {auditor_token}"}
    res = compliance_client.get("/compliance/audit-trail", headers=headers)
    assert res.status_code == 200

# 7. Spoofed X-User-Scopes header is IGNORED
def test_spoofed_user_scopes_header_ignored():
    auditor_token = get_token_for("auditor_jane", "COMPLIANCE_REVIEWER", ["compliance:audit:read"])
    headers = {
        "Authorization": f"Bearer {auditor_token}",
        "X-User-Scopes": "clinician:approve,referral:approve,admin:system"
    }
    payload = {
        "decision": "APPROVED",
        "digital_signature": "SIG-HMAC256-TEST"
    }
    res = workspace_client.post("/workspace/decision/DOC-99482-A", json=payload, headers=headers)
    assert res.status_code == 403

# 8. User token rejected on M2M internal endpoint
def test_user_token_rejected_on_m2m_endpoint():
    clinician_token = get_token_for("dr_smith", "TREATING_CLINICIAN", ["clinician:review", "clinician:approve"])
    headers = {"Authorization": f"Bearer {clinician_token}"}
    payload = {
        "document_id": "DOC-99482-A",
        "patient_id": "PAT-99482",
        "idempotency_key": "IDEM-TEST-001",
        "fhir_resources": []
    }
    res = fhir_client.post("/fhir/write-transaction", json=payload, headers=headers)
    assert res.status_code == 403
    assert "Machine-to-machine service authentication required" in res.json()["detail"]

# 9. Valid M2M token accepted on internal endpoint
def test_valid_m2m_token_accepted_on_internal_endpoint():
    m2m_token = get_m2m_token()
    headers = {"Authorization": f"Bearer {m2m_token}"}
    payload = {
        "document_id": "DOC-99482-A",
        "patient_id": "PAT-99482",
        "idempotency_key": "IDEM-TEST-002",
        "fhir_resources": []
    }
    res = fhir_client.post("/fhir/write-transaction", json=payload, headers=headers)
    assert res.status_code == 200
