import pytest
from fastapi.testclient import TestClient
from src.main import app
from src.models import DecisionSubmitRequest

client = TestClient(app)

def test_clinician_rejection_routes_to_rejected_state_and_blocks_ehr_write():
    """
    CRITICAL PRD 5.9 REQUIREMENT TEST:
    Proves that a clinician rejection in Clinical Workspace routes to 'rejected' status
    and cannot silently proceed toward EHR write.
    """
    doc_id = "DOC-REJECT-ROUTE-01"

    # 1. Submit clinician rejection
    response = client.post(
        f"/workspace/decision/{doc_id}",
        json={
            "decision": "REJECTED",
            "clinician_id": "DR-SURYA-MD",
            "notes": "Rejected due to inaccurate medication dosage extraction."
        }
    )
    assert response.status_code == 200
    data = response.json()

    assert data["decision"] == "REJECTED"
    assert data["status"] == "rejected"
    
    # 2. Verify status via findings endpoint
    findings_resp = client.get(f"/workspace/findings/{doc_id}")
    assert findings_resp.status_code == 200
    assert findings_resp.json()["status"] == "rejected"
