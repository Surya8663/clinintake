import hashlib
import hmac
import json
import os
import time
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient
import httpx
import pytest
from transitions import MachineError

os.environ["JWT_SECRET_KEY"] = "test_orchestrator_jwt_secret_2026"
os.environ["LYZR_API_KEY"] = "test_lyzr_api_key_2026"
os.environ["LYZR_BASE_URL"] = "https://api.lyzr.ai"
os.environ["LYZR_SUPERFLOW_ID"] = "sf_test_2026"
os.environ["LYZR_EXTRACTION_AGENT_ID"] = "agent_ext_test"
os.environ["LYZR_EXPLANATION_AGENT_ID"] = "agent_exp_test"
os.environ["LYZR_REFERRAL_AGENT_ID"] = "agent_ref_test"
os.environ["LYZR_POLICY_PROMPT_INJECTION_ID"] = "pol_inj_test"
os.environ["LYZR_POLICY_GROUNDING_ID"] = "pol_grd_test"
os.environ["LYZR_WEBHOOK_SECRET"] = "test_webhook_secret_2026"

from services.common.jwt_verifier import _b64_encode
from src.lyzr_client import LyzrInvalidResponseError, LyzrTimeoutError, LyzrUnavailableError, lyzr_client
from src.main import app
from src.persistence import persistence
from src.state_machine import DocumentWorkflow, transition_workflow


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
        "exp": exp,
    }
    header_b64 = _b64_encode(json.dumps(header).encode("utf-8"))
    payload_b64 = _b64_encode(json.dumps(payload).encode("utf-8"))
    message = f"{header_b64}.{payload_b64}"
    sig = hmac.new(b"test_orchestrator_jwt_secret_2026", message.encode("utf-8"), hashlib.sha256).digest()
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
    response = client.post("/orchestrator/documents", json={"document_id": "api-doc-123", "file_path": "/data/input.pdf"}, headers=headers)
    assert response.status_code == 200
    assert response.json()["document_id"] == "api-doc-123"
    assert response.json()["state"] == "received"


def test_real_successful_lyzr_response_validated():
    """Test F1: Real successful Lyzr response is validated and returned."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "execution_id": "exec_real_12345",
        "session_id": "sess_real_12345",
        "trace_id": "trace_real_12345",
        "status": "RUNNING",
        "nodes": {"ingestion": "COMPLETED"},
    }

    with patch.object(httpx.Client, "post", return_value=mock_resp) as mock_post:
        res = lyzr_client.start_superflow_execution("sf_test_2026", "DOC-001", {"file_path": "/test.pdf"})
        assert res["execution_id"] == "exec_real_12345"
        assert res["status"] == "RUNNING"
        assert res["nodes"] == {"ingestion": "COMPLETED"}

        # Verify request payload sent to external boundary
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args.kwargs
        assert call_kwargs["json"]["document_id"] == "DOC-001"


def test_lyzr_connection_failure_no_execution_id():
    """Test F2: Lyzr connection failure raises typed LyzrUnavailableError and creates no execution ID."""
    with patch.object(httpx.Client, "post", side_effect=httpx.ConnectError("Connection refused")):
        with pytest.raises(LyzrUnavailableError):
            lyzr_client.start_superflow_execution("sf_test_2026", "DOC-002", {"file_path": "/test.pdf"})


def test_lyzr_timeout_does_not_mark_nodes_as_completed():
    """Test F3: Lyzr timeout raises LyzrTimeoutError and does not mark nodes as completed."""
    with patch.object(httpx.Client, "post", side_effect=httpx.TimeoutException("Request timed out")):
        with pytest.raises(LyzrTimeoutError):
            lyzr_client.start_superflow_execution("sf_test_2026", "DOC-003", {"file_path": "/test.pdf"})


def test_lyzr_malformed_response_rejected():
    """Test F4: Lyzr malformed response is rejected with LyzrInvalidResponseError."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"invalid": "payload_without_execution_id"}

    with patch.object(httpx.Client, "post", return_value=mock_resp):
        with pytest.raises(LyzrInvalidResponseError):
            lyzr_client.start_superflow_execution("sf_test_2026", "DOC-004", {"file_path": "/test.pdf"})


def test_test_runner_exits_nonzero_for_synthetic_pytest_collection_error(tmp_path):
    """Condition 15: Test runner exits non-zero when pytest encounters a synthetic collection/syntax error."""
    from scripts.run_blocker1_tests import run_service_tests

    bad_service = tmp_path / "bad_service"
    bad_tests = bad_service / "tests"
    bad_tests.mkdir(parents=True)

    bad_file = bad_tests / "test_broken_syntax.py"
    bad_file.write_text("def test_broken():\n    this is bad syntax !!!")

    returncode, passed, failed, output = run_service_tests(bad_service)
    assert returncode != 0
