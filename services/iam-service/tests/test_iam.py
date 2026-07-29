import os
from fastapi.testclient import TestClient
os.environ["JWT_SECRET_KEY"] = "test_jwt_secret_key_2026_x99"

from src.main import app

client = TestClient(app)

def test_iam_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["token_ttl_minutes"] == 15

def test_invalid_credentials_rejected():
    """Proves that authentication fails if invalid password is supplied."""
    payload = {
        "username": "dr_smith",
        "password": "WrongPassword!"
    }
    response = client.post("/iam/auth/login", json=payload)
    assert response.status_code == 401
    assert "Invalid credentials" in response.json()["detail"]

def test_valid_oidc_login_issues_short_lived_jwt_with_roles():
    """
    Proves OIDC login generates a short-lived JWT token (15-min TTL) encoded with fine-grained roles.
    """
    payload = {
        "username": "dr_smith",
        "password": "ClinicianPass123!"
    }
    response = client.post("/iam/auth/login", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["token_type"] == "bearer"
    assert data["expires_in_seconds"] == 900
    assert data["role"] == "TREATING_CLINICIAN"
    assert "clinician:approve" in data["scopes"]
    assert "clinician:review" in data["scopes"]

    token = data["access_token"]

    # Verify token with required scope 'clinician:approve'
    v_resp1 = client.post("/iam/auth/verify", json={"token": token, "required_scope": "clinician:approve"})
    assert v_resp1.status_code == 200
    assert v_resp1.json()["valid"] is True
    assert v_resp1.json()["has_scope"] is True

    # Verify token with required scope 'compliance:audit:read' -> has_scope False
    v_resp2 = client.post("/iam/auth/verify", json={"token": token, "required_scope": "compliance:audit:read"})
    assert v_resp2.status_code == 200
    assert v_resp2.json()["valid"] is True
    assert v_resp2.json()["has_scope"] is False

def test_m2m_token_generation():
    """Proves M2M client credentials endpoint issues valid internal service token."""
    payload = {
        "client_id": "clinintake-m2m",
        "client_secret": "sec_keycloak_m2m_secret_2026"
    }
    response = client.post("/iam/auth/token/m2m", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "CLINICAL_AGENT"
    assert "service:internal" in data["scopes"]
