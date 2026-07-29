from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from packages.clinical_contracts.base import BaseClinicalContract
from packages.clinical_contracts.error import ApiErrorEnvelope

class DocumentMetadata(BaseModel):
    file_name: str
    file_path: str
    file_size_bytes: int
    content_type: str = "application/pdf"
    checksum_sha256: Optional[str] = None

class PatientIdentityStatus(BaseModel):
    patient_id: str
    match_confidence: float = 1.0
    status: str = "VERIFIED"  # VERIFIED, UNRESOLVED, QUARANTINED
    demographics: Dict[str, Any] = {}

class OcrEvidence(BaseModel):
    text_content: str
    page_count: int
    bounding_boxes: List[Dict[str, Any]] = []

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
    medications: List[MedicationItem] = []
    diagnoses: List[DiagnosisItem] = []
    labs: List[LabResultItem] = []

class TerminologyMapping(BaseModel):
    source_term: str
    source_code: str
    mapped_system: str  # RxNorm, LOINC, ICD-10-CM, SNOMED-CT
    mapped_code: str
    display_name: str

class ValidationStatus(BaseModel):
    is_valid: bool
    issues: List[Dict[str, Any]] = []
    requires_manual_review: bool = False

class DeterministicOutputs(BaseModel):
    cql_evaluation: Dict[str, Any] = {}
    temporal_gaps: List[Dict[str, Any]] = []
    drug_interactions: List[Dict[str, Any]] = []

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
    alerts: List[Dict[str, Any]] = []
    safety_interrupt: bool = False

class ReferralDraft(BaseModel):
    referral_letter_text: str
    specialty: str
    urgency: str

class GuardrailResult(BaseModel):
    is_grounded: bool = True
    grounding_score: float = 1.0
    flagged_claims: List[str] = []

class ClinicianApproval(BaseModel):
    approved_by: str
    decision: str  # APPROVED, REJECTED
    timestamp_iso: str
    digital_signature: str
    notes: Optional[str] = None

class EhrTransactionResult(BaseModel):
    status: str  # PERSISTED, DUPLICATE_SKIPPED, FAILED
    fhir_bundle_id: Optional[str] = None
    resource_references: List[str] = []

class ClinicalWorkflowContext(BaseClinicalContract):
    """
    Canonical end-to-end workflow context object for document processing.
    Passes through Orchestrator hub and spoke services.
    """
    state: str = Field(default="received", description="Current workflow state")
    document_metadata: Optional[DocumentMetadata] = None
    sanitized_file_path: Optional[str] = None
    patient_identity: Optional[PatientIdentityStatus] = None
    ocr_evidence: Optional[OcrEvidence] = None
    extracted_clinical_data: Optional[ExtractedClinicalData] = None
    terminology_mappings: List[TerminologyMapping] = []
    validation_status: Optional[ValidationStatus] = None
    deterministic_outputs: Optional[DeterministicOutputs] = None
    guideline_evidence: List[GuidelineEvidence] = []
    care_gaps: List[CareGapItem] = []
    safety_state: Optional[SafetyState] = None
    referral_draft: Optional[ReferralDraft] = None
    guardrail_result: Optional[GuardrailResult] = None
    clinician_approval: Optional[ClinicianApproval] = None
    ehr_transaction_result: Optional[EhrTransactionResult] = None
    error_state: Optional[ApiErrorEnvelope] = None
