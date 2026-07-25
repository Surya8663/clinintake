from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_iam_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["token_ttl_minutes"] == 15

def test_invalid_mfa_code_rejected():
    """Proves that authentication fails if invalid MFA code is supplied."""
    payload = {
        "username": "dr_surya",
        "password": "Password123!",
        "mfa_code": "999999" # Invalid MFA code
    }
    response = client.post("/iam/auth/login", json=payload)
    assert response.status_code == 401
    assert "MFA verification code" in response.json()["detail"]

def test_valid_mfa_login_issues_short_lived_jwt_with_scopes():
    """
    CRITICAL PRD 5.1 REQUIREMENT TEST:
    Proves MFA login generates a short-lived JWT token (15-min TTL) encoded with fine-grained scopes.
    """
    payload = {
        "username": "dr_surya",
        "password": "Password123!",
        "mfa_code": "123456" # Valid MFA code
    }
    response = client.post("/iam/auth/login", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["token_type"] == "bearer"
    assert data["expires_in_seconds"] == 900 # 15 min TTL
    assert data["role"] == "TREATING_CLINICIAN"
    assert "referral:approve" in data["scopes"]
    assert "phi:read" in data["scopes"]

    token = data["access_token"]

    # 1. Verify token with required scope 'referral:approve' -> MUST Succeed
    v_resp1 = client.post("/iam/auth/verify", json={"token": token, "required_scope": "referral:approve"})
    assert v_resp1.status_code == 200
    assert v_resp1.json()["valid"] is True
    assert v_resp1.json()["has_scope"] is True

    # 2. Verify token with required scope 'audit:read' -> MUST fail has_scope
    v_resp2 = client.post("/iam/auth/verify", json={"token": token, "required_scope": "audit:read"})
    assert v_resp2.status_code == 200
    assert v_resp2.json()["valid"] is True
    assert v_resp2.json()["has_scope"] is False
