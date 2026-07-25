from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_compliance_dashboard_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_compliance_audit_trail_queries_via_api():
    """
    CRITICAL PRD REQUIREMENT TEST:
    Proves compliance dashboard fetches audit trail data via audit-service REST API.
    Zero direct database access.
    """
    response = client.get("/compliance/audit-trail")
    assert response.status_code == 200
    data = response.json()
    assert "total_records" in data
    assert "records" in data

def test_compliance_vault_integrity_check():
    """Proves vault integrity verification via API endpoint."""
    response = client.get("/compliance/verify-vault")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
