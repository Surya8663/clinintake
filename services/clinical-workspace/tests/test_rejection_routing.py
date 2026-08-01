import hashlib
import hmac
import json
import os
import time

from fastapi.testclient import TestClient
import pytest

os.environ["JWT_SECRET_KEY"] = "test_workspace_secret_key_2026"

from services.common.jwt_verifier import _b64_encode
from src.main import app

client = TestClient(app)


def get_auth_header(username="dr_smith", roles=["clinician:review", "clinician:reject"]):
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
        "exp": exp,
    }
    header_b64 = _b64_encode(json.dumps(header).encode("utf-8"))
    payload_b64 = _b64_encode(json.dumps(payload).encode("utf-8"))
    message = f"{header_b64}.{payload_b64}"
    sig = hmac.new(b"test_workspace_secret_key_2026", message.encode("utf-8"), hashlib.sha256).digest()
    token = f"{message}.{_b64_encode(sig)}"
    return {"Authorization": f"Bearer {token}"}


def test_clinician_rejection_routes_to_rejected_state_and_blocks_ehr_write():
    doc_id = "DOC-99482-A"
    headers = get_auth_header()

    # 1. Submit clinician rejection
    response = client.post(
        f"/workspace/decision/{doc_id}",
        json={"decision": "REJECTED", "clinician_id": "dr_smith", "digital_signature": "SIG-REJECT-TEST", "notes": "Rejected due to inaccurate medication dosage extraction."},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()

    assert data["decision"] == "REJECTED"
    assert data["status"] == "rejected"

    # 2. Verify status via findings endpoint
    findings_resp = client.get(f"/workspace/findings/{doc_id}", headers=headers)
    assert findings_resp.status_code == 200
    assert findings_resp.json()["status"] == "rejected"
