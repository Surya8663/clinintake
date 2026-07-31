import os

from fastapi.testclient import TestClient

os.environ["JWT_SECRET_KEY"] = "test_workspace_secret_key_2026"

import hashlib
import hmac
import json
import time

from services.common.jwt_verifier import _b64_encode
from src.main import app

client = TestClient(app)

def get_auth_header(username="dr_smith", roles=["clinician:review", "clinician:approve", "clinician:reject"]):
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

def test_clinical_workspace_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_get_review_queue_and_findings():
    headers = get_auth_header()
    # 1. Fetch queue
    q_resp = client.get("/workspace/reviews", headers=headers)
    assert q_resp.status_code == 200
    queue = q_resp.json()
    assert len(queue) >= 1

    # 2. Fetch findings with evidence spans & bounding boxes
    doc_id = queue[0]["document_id"]
    f_resp = client.get(f"/workspace/findings/{doc_id}", headers=headers)
    assert f_resp.status_code == 200
    findings = f_resp.json()
    assert findings["document_id"] == doc_id
    assert "referral_text" in findings
    assert len(findings["evidence_spans"]) >= 1
    assert "bbox" in findings["evidence_spans"][0]

def test_edit_referral_text_and_submit_signed_approval():
    headers = get_auth_header()
    doc_id = "DOC-99482-A"
    
    # 1. Save referral text edits
    edit_resp = client.put(
        f"/workspace/referral/{doc_id}",
        json={"edited_referral_text": "Updated referral text by Dr. Smith for Urgent Gastroenterology Evaluation."},
        headers=headers
    )
    assert edit_resp.status_code == 200
    assert edit_resp.json()["status"] == "updated"

    # 2. Submit Signed Approval
    dec_resp = client.post(
        f"/workspace/decision/{doc_id}",
        json={
            "decision": "APPROVED",
            "clinician_id": "dr_smith",
            "digital_signature": "SIG-HMAC256-2026-07-27T17:30:00Z-a3f8c9d2e1b4c5d6e7f8",
            "notes": "Approved for FHIR EHR write."
        },
        headers=headers
    )
    assert dec_resp.status_code == 200
    data = dec_resp.json()
    assert data["decision"] == "APPROVED"
    assert data["status"] == "approved"
    assert data["signed_event_emitted"] is True
