from typing import Any

from transitions import Machine, MachineError

from packages.clinical_contracts import ClinicalWorkflowState
from src.logger import logger


class UnapprovedEHRWriteError(Exception):
    """Raised when an attempt to transition to writing_ehr occurs without signed clinician approval."""

class OptimisticLockError(Exception):
    """Raised when a state transition or save fails due to version mismatch."""

class DocumentWorkflow:
    def __init__(
        self,
        document_id: str,
        state: str = "received",
        context: dict[str, Any] | None = None,
        version: int = 1,
        trace_id: str | None = None,
        correlation_id: str | None = None,
        lyzr_execution_id: str | None = None
    ):
        self.document_id = document_id
        self.state = state
        self.context = context or {}
        self.version = version
        self.trace_id = trace_id
        self.correlation_id = correlation_id
        self.lyzr_execution_id = lyzr_execution_id

class WorkflowMachine:
    STATES = [s.value for s in ClinicalWorkflowState] + [
        "sanitizing", "extracting", "validating", "reasoning", "awaiting_approval", "writing_ehr", "complete", "escalated"
    ]
    
    TRANSITIONS = [
        {"trigger": "start_sanitize", "source": ["received", "failed_retryable"], "dest": "sanitizing"},
        {"trigger": "quarantine", "source": ["received", "security_scanning", "validating", "guardrail_review"], "dest": "quarantined"},
        {"trigger": "start_identity", "source": ["security_scanning", "failed_retryable"], "dest": "identity_resolving"},
        {"trigger": "need_identity_review", "source": "identity_resolving", "dest": "identity_review"},
        {"trigger": "start_ocr", "source": ["identity_resolving", "identity_review", "failed_retryable"], "dest": "ocr_processing"},
        {"trigger": "start_extraction", "source": ["ocr_processing", "failed_retryable"], "dest": "extracting"},
        {"trigger": "start_terminology", "source": ["extracting", "failed_retryable"], "dest": "terminology_normalizing"},
        {"trigger": "start_validation", "source": ["terminology_normalizing", "failed_retryable"], "dest": "validating"},
        {"trigger": "start_reasoning", "source": ["validating", "failed_retryable"], "dest": "deterministic_reasoning"},
        {"trigger": "escalate_safety", "source": "deterministic_reasoning", "dest": "safety_escalated"},
        {"trigger": "assemble_package", "source": ["deterministic_reasoning", "safety_escalated", "failed_retryable"], "dest": "assembling_decision_package"},
        {"trigger": "start_drafting", "source": ["assembling_decision_package", "failed_retryable"], "dest": "drafting"},
        {"trigger": "start_guardrail", "source": ["drafting", "failed_retryable"], "dest": "guardrail_review"},
        {"trigger": "await_clinician", "source": "guardrail_review", "dest": "awaiting_clinician"},
        {"trigger": "reject", "source": ["identity_review", "safety_escalated", "awaiting_clinician", "ehr_authorizing", "awaiting_approval"], "dest": "rejected"},
        {"trigger": "authorize_ehr", "source": ["awaiting_clinician", "awaiting_approval"], "dest": "ehr_authorizing"},
        {"trigger": "start_ehr_write", "source": ["ehr_authorizing", "failed_retryable"], "dest": "ehr_writing"},
        {"trigger": "write_ehr_success", "source": ["ehr_writing", "writing_ehr"], "dest": "complete"},
        {"trigger": "fail_retryable", "source": "*", "dest": "failed_retryable"},
        {"trigger": "fail_terminal", "source": "*", "dest": "failed_terminal"},
        # Aliases for integration tests
        {"trigger": "sanitize_success", "source": ["security_scanning", "sanitizing", "received"], "dest": "extracting"},
        {"trigger": "extraction_success", "source": ["extracting"], "dest": "validating"},
        {"trigger": "validation_success", "source": ["validating"], "dest": "reasoning"},
        {"trigger": "reasoning_needs_review", "source": ["reasoning", "deterministic_reasoning"], "dest": "awaiting_approval"},
        {"trigger": "approve", "source": ["awaiting_approval", "awaiting_clinician"], "dest": "writing_ehr"},
        {"trigger": "force_escalate", "source": "*", "dest": "escalated"},
        {"trigger": "force_reject", "source": "*", "dest": "rejected"},
    ]

    @classmethod
    def get_machine(cls, model: DocumentWorkflow) -> Machine:
        return Machine(
            model=model,
            states=cls.STATES,
            transitions=cls.TRANSITIONS,
            initial=model.state,
            send_event=True,
            auto_transitions=False
        )

def transition_workflow(
    model: DocumentWorkflow,
    trigger: str,
    expected_version: int | None = None,
    *args,
    **kwargs
) -> DocumentWorkflow:
    """
    Attempts to trigger a state transition on DocumentWorkflow with optimistic concurrency control.
    """
    if expected_version is not None and expected_version != model.version:
        logger.error(f"[OPTIMISTIC LOCK FAILURE] Mismatch for doc_id={model.document_id}: expected={expected_version}, current={model.version}")
        raise OptimisticLockError(f"Optimistic lock failure: expected version {expected_version}, current {model.version}")

    if trigger in ("authorize_ehr", "start_ehr_write", "approve"):
        is_signed = model.context.get("signed_approval") or kwargs.get("signed_approval")
        if not is_signed:
            logger.error(f"Governance Violation: Blocked attempt to write EHR without signed approval for doc_id={model.document_id}")
            raise UnapprovedEHRWriteError("Governance Violation: Cannot transition to writing_ehr without genuine Signed Approval event.")

    machine = WorkflowMachine.get_machine(model)
    logger.info(
        f"Attempting transition: {trigger} (v{model.version})",
        extra={
            "document_id": model.document_id,
            "current_state": model.state,
            "trigger": trigger,
            "version": model.version
        }
    )
    
    try:
        trigger_func = getattr(model, trigger)
        trigger_func(*args, **kwargs)
        model.version += 1
    except MachineError as e:
        logger.error(
            f"Invalid transition attempted: {trigger}",
            extra={
                "document_id": model.document_id,
                "current_state": model.state,
                "trigger": trigger,
                "error": str(e)
            }
        )
        raise e
        
    logger.info(
        f"Transition successful: {trigger} -> {model.state} (v{model.version})",
        extra={
            "document_id": model.document_id,
            "new_state": model.state,
            "version": model.version
        }
    )
    return model
