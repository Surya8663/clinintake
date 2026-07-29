import os
import sys
import uuid
import hmac
import hashlib
import pytest
from pathlib import Path

os.environ["JWT_SECRET_KEY"] = "test_jwt_secret_key_2026"
os.environ["ENCRYPTION_KEY"] = "test_kms_encryption_key_32_bytes_len"
from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
import importlib

for k in list(sys.modules.keys()):
    if k == 'src' or k.startswith('src.'):
        del sys.modules[k]

sys.path.insert(0, str(REPO_ROOT / "services" / "orchestrator"))

from packages.clinical_contracts import ClinicalWorkflowState, is_valid_transition
orch_sm = importlib.import_module("services.orchestrator.src.state_machine")
DocumentWorkflow = orch_sm.DocumentWorkflow
transition_workflow = orch_sm.transition_workflow
OptimisticLockError = orch_sm.OptimisticLockError

orch_main = importlib.import_module("services.orchestrator.src.main")
orchestrator_app = orch_main.app
orch_client = TestClient(orchestrator_app)

def test_e2e_full_workflow_timeline():
    document_id = f"DOC-E2E-{uuid.uuid4().hex[:8]}"
    trace_id = f"tr_{uuid.uuid4().hex[:16]}"
    correlation_id = f"corr_{uuid.uuid4().hex[:16]}"
    
    timeline = []

    # 1. State: RECEIVED
    workflow = DocumentWorkflow(
        document_id=document_id,
        state=ClinicalWorkflowState.RECEIVED.value,
        context={"file_path": f"kms_encrypted/{document_id}.enc"},
        version=1,
        trace_id=trace_id,
        correlation_id=correlation_id
    )
    timeline.append((workflow.state, workflow.version))

    # 2. Transition: SECURITY_SCANNING
    workflow = transition_workflow(workflow, "start_sanitize")
    timeline.append((workflow.state, workflow.version))
    assert workflow.state == ClinicalWorkflowState.SECURITY_SCANNING.value

    # 3. Transition: IDENTITY_RESOLVING
    workflow = transition_workflow(workflow, "start_identity")
    timeline.append((workflow.state, workflow.version))

    # 4. Transition: OCR_PROCESSING
    workflow = transition_workflow(workflow, "start_ocr")
    timeline.append((workflow.state, workflow.version))

    # 5. Transition: EXTRACTING
    workflow = transition_workflow(workflow, "start_extraction")
    timeline.append((workflow.state, workflow.version))

    # 6. Transition: TERMINOLOGY_NORMALIZING
    workflow = transition_workflow(workflow, "start_terminology")
    timeline.append((workflow.state, workflow.version))

    # 7. Transition: VALIDATING
    workflow = transition_workflow(workflow, "start_validation")
    timeline.append((workflow.state, workflow.version))

    # 8. Transition: DETERMINISTIC_REASONING
    workflow = transition_workflow(workflow, "start_reasoning")
    timeline.append((workflow.state, workflow.version))

    # 9. Transition: ASSEMBLING_DECISION_PACKAGE
    workflow = transition_workflow(workflow, "assemble_package")
    timeline.append((workflow.state, workflow.version))

    # 10. Transition: DRAFTING
    workflow = transition_workflow(workflow, "start_drafting")
    timeline.append((workflow.state, workflow.version))

    # 11. Transition: GUARDRAIL_REVIEW
    workflow = transition_workflow(workflow, "start_guardrail")
    timeline.append((workflow.state, workflow.version))

    # 12. Transition: AWAITING_CLINICIAN
    workflow = transition_workflow(workflow, "await_clinician")
    timeline.append((workflow.state, workflow.version))
    assert workflow.state == ClinicalWorkflowState.AWAITING_CLINICIAN.value

    # 13. Clinician Signed Approval -> Transition: EHR_AUTHORIZING
    workflow.context["signed_approval"] = True
    workflow = transition_workflow(workflow, "authorize_ehr")
    timeline.append((workflow.state, workflow.version))

    # 14. Transition: EHR_WRITING
    workflow = transition_workflow(workflow, "start_ehr_write")
    timeline.append((workflow.state, workflow.version))

    # 15. Transition: COMPLETED
    workflow = transition_workflow(workflow, "write_ehr_success")
    timeline.append((workflow.state, workflow.version))
    assert workflow.state == ClinicalWorkflowState.COMPLETED.value

    print("\n==================================================")
    print(" FULL E2E WORKFLOW STATE TIMELINE")
    print("==================================================")
    for idx, (st, ver) in enumerate(timeline):
        print(f"Step {idx + 1:02d}: State = {st:<28} Version = {ver}")
    print("==================================================")

def test_optimistic_locking_concurrency_conflict():
    document_id = f"DOC-OPT-{uuid.uuid4().hex[:8]}"
    workflow = DocumentWorkflow(document_id=document_id, state="received", version=1)

    # Attempting transition with wrong expected_version raises OptimisticLockError
    with pytest.raises(OptimisticLockError):
        transition_workflow(workflow, "start_sanitize", expected_version=99)

def test_duplicate_callback_replay_protection():
    secret = "sec_lyzr_webhook_hmac_2026"
    body = b'{"document_id": "DOC-REPLAY-101", "node_id": "extraction_agent", "status": "COMPLETED"}'
    valid_sig = hmac.new(secret.encode('utf-8'), body, hashlib.sha256).hexdigest()

    # 1. First Webhook Callback Call
    res1 = orch_client.post(
        "/orchestrator/webhooks/lyzr-callback",
        content=body,
        headers={"X-Lyzr-Signature": valid_sig, "Content-Type": "application/json"}
    )
    assert res1.status_code == 200
    assert res1.json()["replay"] is False

    # 2. Duplicate Webhook Callback Call (Replay)
    res2 = orch_client.post(
        "/orchestrator/webhooks/lyzr-callback",
        content=body,
        headers={"X-Lyzr-Signature": valid_sig, "Content-Type": "application/json"}
    )
    assert res2.status_code == 200
    assert res2.json()["replay"] is True

def test_non_retryable_validation_failure_routing():
    invalid_state = "invalid_state_xyz"
    assert is_valid_transition("received", invalid_state) is False

def test_retryable_dependency_interruption_recovery():
    # Test retryable state transition to FAILED_RETRYABLE and back
    wf = DocumentWorkflow(document_id="DOC-RETRY-1", state="security_scanning", version=1)
    wf = transition_workflow(wf, "fail_retryable")
    assert wf.state == ClinicalWorkflowState.FAILED_RETRYABLE.value
    
    # Recover from FAILED_RETRYABLE back to security_scanning
    wf = transition_workflow(wf, "start_sanitize")
    assert wf.state == ClinicalWorkflowState.SECURITY_SCANNING.value
