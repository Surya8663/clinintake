from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_rbac_missing_referral_approve_scope_returns_403_forbidden():
    """
    CRITICAL PRD 5.1 REQUIREMENT TEST:
    Proves that attempting a clinician approval decision without the required 'referral:approve' RBAC scope
    is rejected with HTTP 403 Forbidden.
    """
    doc_id = "DOC-RBAC-DENIED-01"
    payload = {
        "decision": "APPROVED",
        "clinician_id": "auditor_jane",
        "notes": "Auditor attempting approval"
    }

    # Pass scope 'audit:read' only (lacks 'referral:approve')
    headers = {"X-User-Scopes": "audit:read"}

    response = client.post(f"/workspace/decision/{doc_id}", json=payload, headers=headers)
    assert response.status_code == 403
    assert "Missing required RBAC scope 'referral:approve'" in response.json()["detail"]

def test_rbac_valid_referral_approve_scope_granted():
    """Proves that passing the required 'referral:approve' RBAC scope grants access."""
    doc_id = "DOC-RBAC-GRANTED-01"
    payload = {
        "decision": "APPROVED",
        "clinician_id": "dr_surya",
        "notes": "Approved by treating clinician"
    }

    # Pass valid scope 'referral:approve'
    headers = {"X-User-Scopes": "phi:read, referral:approve"}

    response = client.post(f"/workspace/decision/{doc_id}", json=payload, headers=headers)
    assert response.status_code == 200
    assert response.json()["decision"] == "APPROVED"
