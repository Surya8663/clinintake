import hashlib
import hmac
import json
import os
import time

from fastapi.testclient import TestClient

os.environ["JWT_SECRET_KEY"] = "test_compliance_secret_key_2026"

from services.common.jwt_verifier import _b64_encode
from src.main import app

client = TestClient(app)

def get_auth_header():
    now = int(time.time())
    exp = now + 900
    roles = ["compliance:audit:read"]
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": "auditor_jane",
        "preferred_username": "auditor_jane",
        "role": "COMPLIANCE_REVIEWER",
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
    sig = hmac.new(b"test_compliance_secret_key_2026", message.encode('utf-8'), hashlib.sha256).digest()
    token = f"{message}.{_b64_encode(sig)}"
    return {"Authorization": f"Bearer {token}"}

def test_compliance_dashboard_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_compliance_audit_trail_queries_via_api():
    headers = get_auth_header()
    response = client.get("/compliance/audit-trail", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "total_records" in data
    assert "records" in data

def test_compliance_vault_integrity_check():
    headers = get_auth_header()
    response = client.get("/compliance/verify-vault", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
