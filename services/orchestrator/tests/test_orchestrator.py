import os
import time, json, hmac, hashlib
import pytest
from fastapi.testclient import TestClient
from transitions import MachineError
from unittest.mock import AsyncMock, patch

os.environ["JWT_SECRET_KEY"] = "test_orchestrator_jwt_secret_2026"

from src.main import app
from src.state_machine import DocumentWorkflow, transition_workflow
from src.persistence import persistence
from services.common.jwt_verifier import _b64_encode

def get_auth_header():
    now = int(time.time())
    exp = now + 3600
    scopes = ["service:internal"]
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": "service:orchestrator",
        "client_id": "clinintake-m2m",
        "role": "CLINICAL_AGENT",
        "roles": scopes,
        "realm_access": {"roles": scopes},
        "scopes": scopes,
        "iss": "http://localhost:8085/realms/clinintake",
        "aud": "clinintake-backend-services",
        "iat": now,
        "exp": exp
    }
    header_b64 = _b64_encode(json.dumps(header).encode('utf-8'))
    payload_b64 = _b64_encode(json.dumps(payload).encode('utf-8'))
    message = f"{header_b64}.{payload_b64}"
    sig = hmac.new(b"test_orchestrator_jwt_secret_2026", message.encode('utf-8'), hashlib.sha256).digest()
    token = f"{message}.{_b64_encode(sig)}"
    return {"Authorization": f"Bearer {token}"}

def test_valid_transitions():
    wf = DocumentWorkflow(document_id="test-doc-1")
    assert wf.state == "received"
    
    transition_workflow(wf, "start_sanitize")
    assert wf.state == "sanitizing"
    
    transition_workflow(wf, "sanitize_success")
    assert wf.state == "extracting"
    
    transition_workflow(wf, "extraction_success")
    assert wf.state == "validating"
    
    transition_workflow(wf, "validation_success")
    assert wf.state == "reasoning"
    
    transition_workflow(wf, "reasoning_needs_review")
    assert wf.state == "awaiting_approval"
    
    wf.context["signed_approval"] = True
    transition_workflow(wf, "approve")
    assert wf.state == "writing_ehr"
    
    transition_workflow(wf, "write_ehr_success")
    assert wf.state == "complete"

def test_invalid_transitions():
    wf = DocumentWorkflow(document_id="test-doc-2")
    assert wf.state == "received"
    
    with pytest.raises(MachineError):
        transition_workflow(wf, "write_ehr_success")
        
    with pytest.raises(MachineError):
        transition_workflow(wf, "extraction_success")

def test_global_transitions():
    wf = DocumentWorkflow(document_id="test-doc-3")
    assert wf.state == "received"
    
    transition_workflow(wf, "force_escalate")
    assert wf.state == "escalated"
    
    wf2 = DocumentWorkflow(document_id="test-doc-4", state="awaiting_approval")
    transition_workflow(wf2, "force_reject")
    assert wf2.state == "rejected"

@patch("src.persistence.persistence.client")
@pytest.mark.asyncio
async def test_persistence_save_load(mock_redis_client):
    mock_db = {}
    
    async def mock_set(key, val):
        mock_db[key] = val
        return True
        
    async def mock_get(key):
        return mock_db.get(key)
        
    mock_redis = AsyncMock()
    mock_redis.set = mock_set
    mock_redis.get = mock_get
    
    with patch("src.persistence.persistence.get_client", return_value=mock_redis):
        wf = DocumentWorkflow(document_id="test-persist", state="received", context={"file_path": "/path/to/raw"})
        await persistence.save_workflow(wf)
        
        loaded = await persistence.get_workflow("test-persist")
        assert loaded is not None
        assert loaded.document_id == "test-persist"
        assert loaded.state == "received"
        assert loaded.context["file_path"] == "/path/to/raw"

def test_api_health():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "workflow-orchestrator"}

@patch("src.persistence.persistence.get_client")
@patch("src.dispatcher.audit_event_bus.publish_event")
def test_api_create_document(mock_publish, mock_get_client):
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None
    mock_get_client.return_value = mock_redis
    
    client = TestClient(app)
    headers = get_auth_header()
    response = client.post(
        "/orchestrator/documents",
        json={"document_id": "api-doc-123", "file_path": "/data/input.pdf"},
        headers=headers
    )
    assert response.status_code == 200
    assert response.json()["document_id"] == "api-doc-123"
    assert response.json()["state"] == "received"
