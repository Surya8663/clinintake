from enum import Enum
from typing import Dict, Set

class ClinicalWorkflowState(str, Enum):
    RECEIVED = "received"
    SECURITY_SCANNING = "security_scanning"
    QUARANTINED = "quarantined"
    IDENTITY_RESOLVING = "identity_resolving"
    IDENTITY_REVIEW = "identity_review"
    OCR_PROCESSING = "ocr_processing"
    EXTRACTING = "extracting"
    TERMINOLOGY_NORMALIZING = "terminology_normalizing"
    VALIDATING = "validating"
    DETERMINISTIC_REASONING = "deterministic_reasoning"
    SAFETY_ESCALATED = "safety_escalated"
    ASSEMBLING_DECISION_PACKAGE = "assembling_decision_package"
    DRAFTING = "drafting"
    GUARDRAIL_REVIEW = "guardrail_review"
    AWAITING_CLINICIAN = "awaiting_clinician"
    REJECTED = "rejected"
    EHR_AUTHORIZING = "ehr_authorizing"
    EHR_WRITING = "ehr_writing"
    COMPLETED = "completed"
    FAILED_RETRYABLE = "failed_retryable"
    FAILED_TERMINAL = "failed_terminal"

# Authoritative State Transition Graph
VALID_STATE_TRANSITIONS: Dict[ClinicalWorkflowState, Set[ClinicalWorkflowState]] = {
    ClinicalWorkflowState.RECEIVED: {
        ClinicalWorkflowState.SECURITY_SCANNING,
        ClinicalWorkflowState.QUARANTINED,
        ClinicalWorkflowState.FAILED_TERMINAL
    },
    ClinicalWorkflowState.SECURITY_SCANNING: {
        ClinicalWorkflowState.QUARANTINED,
        ClinicalWorkflowState.IDENTITY_RESOLVING,
        ClinicalWorkflowState.FAILED_RETRYABLE,
        ClinicalWorkflowState.FAILED_TERMINAL
    },
    ClinicalWorkflowState.IDENTITY_RESOLVING: {
        ClinicalWorkflowState.IDENTITY_REVIEW,
        ClinicalWorkflowState.OCR_PROCESSING,
        ClinicalWorkflowState.FAILED_RETRYABLE,
        ClinicalWorkflowState.FAILED_TERMINAL
    },
    ClinicalWorkflowState.IDENTITY_REVIEW: {
        ClinicalWorkflowState.OCR_PROCESSING,
        ClinicalWorkflowState.REJECTED,
        ClinicalWorkflowState.FAILED_TERMINAL
    },
    ClinicalWorkflowState.OCR_PROCESSING: {
        ClinicalWorkflowState.EXTRACTING,
        ClinicalWorkflowState.FAILED_RETRYABLE,
        ClinicalWorkflowState.FAILED_TERMINAL
    },
    ClinicalWorkflowState.EXTRACTING: {
        ClinicalWorkflowState.TERMINOLOGY_NORMALIZING,
        ClinicalWorkflowState.FAILED_RETRYABLE,
        ClinicalWorkflowState.FAILED_TERMINAL
    },
    ClinicalWorkflowState.TERMINOLOGY_NORMALIZING: {
        ClinicalWorkflowState.VALIDATING,
        ClinicalWorkflowState.FAILED_RETRYABLE,
        ClinicalWorkflowState.FAILED_TERMINAL
    },
    ClinicalWorkflowState.VALIDATING: {
        ClinicalWorkflowState.DETERMINISTIC_REASONING,
        ClinicalWorkflowState.QUARANTINED,
        ClinicalWorkflowState.FAILED_RETRYABLE,
        ClinicalWorkflowState.FAILED_TERMINAL
    },
    ClinicalWorkflowState.DETERMINISTIC_REASONING: {
        ClinicalWorkflowState.SAFETY_ESCALATED,
        ClinicalWorkflowState.ASSEMBLING_DECISION_PACKAGE,
        ClinicalWorkflowState.FAILED_RETRYABLE,
        ClinicalWorkflowState.FAILED_TERMINAL
    },
    ClinicalWorkflowState.SAFETY_ESCALATED: {
        ClinicalWorkflowState.ASSEMBLING_DECISION_PACKAGE,
        ClinicalWorkflowState.REJECTED,
        ClinicalWorkflowState.FAILED_TERMINAL
    },
    ClinicalWorkflowState.ASSEMBLING_DECISION_PACKAGE: {
        ClinicalWorkflowState.DRAFTING,
        ClinicalWorkflowState.FAILED_RETRYABLE,
        ClinicalWorkflowState.FAILED_TERMINAL
    },
    ClinicalWorkflowState.DRAFTING: {
        ClinicalWorkflowState.GUARDRAIL_REVIEW,
        ClinicalWorkflowState.FAILED_RETRYABLE,
        ClinicalWorkflowState.FAILED_TERMINAL
    },
    ClinicalWorkflowState.GUARDRAIL_REVIEW: {
        ClinicalWorkflowState.AWAITING_CLINICIAN,
        ClinicalWorkflowState.QUARANTINED,
        ClinicalWorkflowState.FAILED_TERMINAL
    },
    ClinicalWorkflowState.AWAITING_CLINICIAN: {
        ClinicalWorkflowState.EHR_AUTHORIZING,
        ClinicalWorkflowState.REJECTED,
        ClinicalWorkflowState.FAILED_TERMINAL
    },
    ClinicalWorkflowState.EHR_AUTHORIZING: {
        ClinicalWorkflowState.EHR_WRITING,
        ClinicalWorkflowState.REJECTED,
        ClinicalWorkflowState.FAILED_TERMINAL
    },
    ClinicalWorkflowState.EHR_WRITING: {
        ClinicalWorkflowState.COMPLETED,
        ClinicalWorkflowState.FAILED_RETRYABLE,
        ClinicalWorkflowState.FAILED_TERMINAL
    },
    ClinicalWorkflowState.FAILED_RETRYABLE: {
        ClinicalWorkflowState.SECURITY_SCANNING,
        ClinicalWorkflowState.IDENTITY_RESOLVING,
        ClinicalWorkflowState.OCR_PROCESSING,
        ClinicalWorkflowState.EXTRACTING,
        ClinicalWorkflowState.TERMINOLOGY_NORMALIZING,
        ClinicalWorkflowState.VALIDATING,
        ClinicalWorkflowState.DETERMINISTIC_REASONING,
        ClinicalWorkflowState.ASSEMBLING_DECISION_PACKAGE,
        ClinicalWorkflowState.DRAFTING,
        ClinicalWorkflowState.GUARDRAIL_REVIEW,
        ClinicalWorkflowState.EHR_WRITING,
        ClinicalWorkflowState.FAILED_TERMINAL
    },
    ClinicalWorkflowState.QUARANTINED: set(),
    ClinicalWorkflowState.REJECTED: set(),
    ClinicalWorkflowState.COMPLETED: set(),
    ClinicalWorkflowState.FAILED_TERMINAL: set()
}

def is_valid_transition(current_state: str, new_state: str) -> bool:
    try:
        curr_enum = ClinicalWorkflowState(current_state)
        new_enum = ClinicalWorkflowState(new_state)
        return new_enum in VALID_STATE_TRANSITIONS.get(curr_enum, set())
    except ValueError:
        return False
