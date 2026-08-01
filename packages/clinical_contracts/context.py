from typing import Any

from pydantic import BaseModel, Field

from packages.clinical_contracts.base import BaseClinicalContract
from packages.clinical_contracts.error import ApiErrorEnvelope


class DocumentMetadata(BaseModel):
    file_name: str
    file_path: str
    file_size_bytes: int
    content_type: str = "application/pdf"
    checksum_sha256: str | None = None


class PatientIdentityStatus(BaseModel):
    patient_id: str
    match_confidence: float = 1.0
    status: str = "VERIFIED"  # VERIFIED, UNRESOLVED, QUARANTINED
    demographics: dict[str, Any] = {}


class OcrEvidence(BaseModel):
    text_content: str
    page_count: int
    bounding_boxes: list[dict[str, Any]] = []


class MedicationItem(BaseModel):
    name: str
    rxnorm_code: str
    dosage: str
    frequency: str


class DiagnosisItem(BaseModel):
    name: str
    icd10_code: str
    confidence: float


class LabResultItem(BaseModel):
    name: str
    loinc_code: str
    value: str
    unit: str


class ExtractedClinicalData(BaseModel):
    medications: list[MedicationItem] = []
    diagnoses: list[DiagnosisItem] = []
    labs: list[LabResultItem] = []


class TerminologyMapping(BaseModel):
    source_term: str
    source_code: str
    mapped_system: str  # RxNorm, LOINC, ICD-10-CM, SNOMED-CT
    mapped_code: str
    display_name: str


class ValidationStatus(BaseModel):
    is_valid: bool
    issues: list[dict[str, Any]] = []
    requires_manual_review: bool = False


class DeterministicOutputs(BaseModel):
    cql_evaluation: dict[str, Any] = {}
    temporal_gaps: list[dict[str, Any]] = []
    drug_interactions: list[dict[str, Any]] = []


class GuidelineEvidence(BaseModel):
    guideline_id: str
    title: str
    evidence_quote: str
    section: str


class CareGapItem(BaseModel):
    gap_id: str
    title: str
    evidence: str
    suggested_action: str
    status: str = "OPEN"


class SafetyState(BaseModel):
    is_emergency: bool = False
    alerts: list[dict[str, Any]] = []
    safety_interrupt: bool = False


class ReferralDraft(BaseModel):
    referral_letter_text: str
    specialty: str
    urgency: str


class GuardrailResult(BaseModel):
    is_grounded: bool = True
    grounding_score: float = 1.0
    flagged_claims: list[str] = []


class ClinicianApproval(BaseModel):
    approved_by: str
    decision: str  # APPROVED, REJECTED
    timestamp_iso: str
    digital_signature: str
    notes: str | None = None


class EhrTransactionResult(BaseModel):
    status: str  # PERSISTED, DUPLICATE_SKIPPED, FAILED
    fhir_bundle_id: str | None = None
    resource_references: list[str] = []


class ClinicalWorkflowContext(BaseClinicalContract):
    """
    Canonical end-to-end workflow context object for document processing.
    Passes through Orchestrator hub and spoke services.
    """

    state: str = Field(default="received", description="Current workflow state")
    document_metadata: DocumentMetadata | None = None
    sanitized_file_path: str | None = None
    patient_identity: PatientIdentityStatus | None = None
    ocr_evidence: OcrEvidence | None = None
    extracted_clinical_data: ExtractedClinicalData | None = None
    terminology_mappings: list[TerminologyMapping] = []
    validation_status: ValidationStatus | None = None
    deterministic_outputs: DeterministicOutputs | None = None
    guideline_evidence: list[GuidelineEvidence] = []
    care_gaps: list[CareGapItem] = []
    safety_state: SafetyState | None = None
    referral_draft: ReferralDraft | None = None
    guardrail_result: GuardrailResult | None = None
    clinician_approval: ClinicianApproval | None = None
    ehr_transaction_result: EhrTransactionResult | None = None
    error_state: ApiErrorEnvelope | None = None
