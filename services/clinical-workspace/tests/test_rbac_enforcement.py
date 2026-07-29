import os
import time, json, hmac, hashlib
from fastapi.testclient import TestClient

os.environ["JWT_SECRET_KEY"] = "test_workspace_secret_key_2026"

from src.main import app
from services.common.jwt_verifier import _b64_encode

client = TestClient(app)

def get_auth_header(username="dr_smith", roles=["clinician:review", "clinician:approve"]):
    now = int(time.time())
    exp = now + 900
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": username,
        "preferred_username": username,
        "role": "TREATING_CLINICIAN",
        "roles": roles,
        "realm_access": {"roles": roles},
        "scopes": roles,
        "scope": " ".join(roles),
        "iss": "http://localhost:8085/realms/clinintake",
        "aud": "clinintake-bff",
        "iat": now,
        "exp": exp
    }
    header_b64 = _b64_encode(json.dumps(header).encode('utf-8'))
    payload_b64 = _b64_encode(json.dumps(payload).encode('utf-8'))
    message = f"{header_b64}.{payload_b64}"
    sig = hmac.new(b"test_workspace_secret_key_2026", message.encode('utf-8'), hashlib.sha256).digest()
    token = f"{message}.{_b64_encode(sig)}"
    return {"Authorization": f"Bearer {token}"}

def test_rbac_missing_referral_approve_scope_returns_403_forbidden():
    doc_id = "DOC-99482-A"
    payload = {
        "decision": "APPROVED",
        "clinician_id": "auditor_jane",
        "digital_signature": "SIG-TEST",
        "notes": "Auditor attempting approval"
    }

    # Pass auditor token (lacks clinician:approve)
    headers = get_auth_header(username="auditor_jane", roles=["compliance:audit:read"])

    response = client.post(f"/workspace/decision/{doc_id}", json=payload, headers=headers)
    assert response.status_code == 403
    assert "Insufficient privileges" in response.json()["detail"]

def test_rbac_valid_referral_approve_scope_granted():
    doc_id = "DOC-99482-A"
    payload = {
        "decision": "APPROVED",
        "clinician_id": "dr_smith",
        "digital_signature": "SIG-TEST",
        "notes": "Approved by treating clinician"
    }

    headers = get_auth_header(username="dr_smith", roles=["clinician:review", "clinician:approve"])

    response = client.post(f"/workspace/decision/{doc_id}", json=payload, headers=headers)
    assert response.status_code == 200
    assert response.json()["decision"] == "APPROVED"
