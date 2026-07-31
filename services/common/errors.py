"""
Structured error types for the ClinIntake platform.
Every service must raise typed errors that are mapped to HTTP status codes
and audit event payloads. Never catch broad exceptions and continue as success.
"""
from enum import Enum
from typing import Optional


class ErrorCode(str, Enum):
    # Authentication & Authorization
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    ROLE_INSUFFICIENT = "ROLE_INSUFFICIENT"
    STEP_UP_REQUIRED = "STEP_UP_REQUIRED"

    # Document & OCR
    DOCUMENT_NOT_FOUND = "DOCUMENT_NOT_FOUND"
    MALWARE_DETECTED = "MALWARE_DETECTED"
    OCR_EXTRACTION_FAILED = "OCR_EXTRACTION_FAILED"
    UNSUPPORTED_DOCUMENT_FORMAT = "UNSUPPORTED_DOCUMENT_FORMAT"

    # Clinical Processing
    PATIENT_IDENTITY_MISMATCH = "PATIENT_IDENTITY_MISMATCH"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    INSUFFICIENT_GUIDELINE_EVIDENCE = "INSUFFICIENT_GUIDELINE_EVIDENCE"
    CONFLICTING_GUIDELINES = "CONFLICTING_GUIDELINES"
    DRUG_INTERACTION_DETECTED = "DRUG_INTERACTION_DETECTED"
    RED_FLAG_EMERGENCY = "RED_FLAG_EMERGENCY"

    # Guardrails & Safety
    PROMPT_INJECTION_DETECTED = "PROMPT_INJECTION_DETECTED"
    UNSUPPORTED_CITATION = "UNSUPPORTED_CITATION"

    # EHR & Write Authorization
    EHR_WRITE_UNAUTHORIZED = "EHR_WRITE_UNAUTHORIZED"
    EHR_WRITE_STALE_PACKAGE = "EHR_WRITE_STALE_PACKAGE"
    EHR_WRITE_IDEMPOTENCY_CONFLICT = "EHR_WRITE_IDEMPOTENCY_CONFLICT"
    EHR_CONNECTION_FAILED = "EHR_CONNECTION_FAILED"

    # Infrastructure
    DEPENDENCY_UNAVAILABLE = "DEPENDENCY_UNAVAILABLE"
    CIRCUIT_BREAKER_OPEN = "CIRCUIT_BREAKER_OPEN"
    AUDIT_VAULT_IMMUTABLE = "AUDIT_VAULT_IMMUTABLE"
    WORKFLOW_STATE_CONFLICT = "WORKFLOW_STATE_CONFLICT"
    DLQ_ESCALATED = "DLQ_ESCALATED"


class ClinIntakeError(Exception):
    """Base exception for all ClinIntake typed errors."""
    def __init__(
        self,
        code: ErrorCode,
        message: str,
        document_id: Optional[str] = None,
        trace_id: Optional[str] = None,
    ):
        self.code = code
        self.message = message
        self.document_id = document_id
        self.trace_id = trace_id
        super().__init__(f"[{code}] {message}")

    def to_dict(self) -> dict:
        return {
            "error_code": self.code.value,
            "message": self.message,
            "document_id": self.document_id,
            "trace_id": self.trace_id,
        }


class AuthenticationError(ClinIntakeError):
    def __init__(self, message: str, **kwargs):
        super().__init__(ErrorCode.UNAUTHORIZED, message, **kwargs)


class RoleInsufficientError(ClinIntakeError):
    def __init__(self, required_role: str, **kwargs):
        super().__init__(ErrorCode.ROLE_INSUFFICIENT, f"Required role: {required_role}", **kwargs)


class MalwareDetectedError(ClinIntakeError):
    def __init__(self, **kwargs):
        super().__init__(ErrorCode.MALWARE_DETECTED, "Malware detected in uploaded document.", **kwargs)


class PatientIdentityMismatchError(ClinIntakeError):
    def __init__(self, **kwargs):
        super().__init__(ErrorCode.PATIENT_IDENTITY_MISMATCH, "Patient identity verification failed.", **kwargs)


class InsufficientGuidelineEvidenceError(ClinIntakeError):
    def __init__(self, measure: str, **kwargs):
        super().__init__(
            ErrorCode.INSUFFICIENT_GUIDELINE_EVIDENCE,
            f"Insufficient guideline evidence for measure: {measure}",
            **kwargs
        )


class PromptInjectionDetectedError(ClinIntakeError):
    def __init__(self, **kwargs):
        super().__init__(
            ErrorCode.PROMPT_INJECTION_DETECTED,
            "Adversarial prompt injection detected. Document quarantined for security review.",
            **kwargs
        )


class EHRWriteUnauthorizedError(ClinIntakeError):
    def __init__(self, **kwargs):
        super().__init__(
            ErrorCode.EHR_WRITE_UNAUTHORIZED,
            "EHR write requires orchestrator-issued write authorization token bound to this document.",
            **kwargs
        )


class DependencyUnavailableError(ClinIntakeError):
    def __init__(self, service_name: str, **kwargs):
        super().__init__(
            ErrorCode.DEPENDENCY_UNAVAILABLE,
            f"Required dependency '{service_name}' is unavailable. Workflow preserved for retry.",
            **kwargs
        )
