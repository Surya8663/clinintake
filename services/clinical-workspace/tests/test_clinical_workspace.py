from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_clinical_workspace_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_get_review_queue_and_findings():
    # 1. Fetch queue
    q_resp = client.get("/workspace/reviews")
    assert q_resp.status_code == 200
    queue = q_resp.json()
    assert len(queue) >= 1

    # 2. Fetch findings with evidence spans & bounding boxes
    doc_id = queue[0]["document_id"]
    f_resp = client.get(f"/workspace/findings/{doc_id}")
    assert f_resp.status_code == 200
    findings = f_resp.json()
    assert findings["document_id"] == doc_id
    assert "referral_text" in findings
    assert len(findings["evidence_spans"]) >= 1
    assert "bbox" in findings["evidence_spans"][0]

def test_edit_referral_text_and_submit_signed_approval():
    doc_id = "DOC-TEST-APPROVAL-01"
    
    # 1. Save referral text edits
    edit_resp = client.put(
        f"/workspace/referral/{doc_id}",
        json={"edited_referral_text": "Updated referral text by Dr. Surya for Urgent Gastroenterology Evaluation."}
    )
    assert edit_resp.status_code == 200
    assert edit_resp.json()["status"] == "updated"

    # 2. Submit Signed Approval
    dec_resp = client.post(
        f"/workspace/decision/{doc_id}",
        json={
            "decision": "APPROVED",
            "clinician_id": "DR-SURYA-MD",
            "digital_signature": "SIG-HMAC256-2026-07-27T17:30:00Z-a3f8c9d2e1b4c5d6e7f8",
            "notes": "Approved for FHIR EHR write."
        }
    )
    assert dec_resp.status_code == 200
    data = dec_resp.json()
    assert data["decision"] == "APPROVED"
    assert data["status"] == "approved"
    assert data["signed_event_emitted"] is True
