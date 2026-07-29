from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from packages.clinical_contracts.base import BaseClinicalContract

# 1. Document Security Filter (/filter/scan)
class FilterScanRequest(BaseClinicalContract):
    file_path: str = Field(..., description="Absolute file path to target PDF document")

class FilterScanResponse(BaseClinicalContract):
    is_safe: bool = Field(..., description="Safety filter validation result")
    threat_level: str = Field(default="NONE", description="Detected threat classification")
    sanitized_file_path: Optional[str] = Field(default=None, description="Path to clean sanitized document")
    quarantine_reason: Optional[str] = Field(default=None, description="Reason if document was quarantined")

# 2. OCR Service (/ocr/process)
class OcrProcessRequest(BaseClinicalContract):
    file_path: str = Field(..., description="File path to sanitized PDF document")

class OcrProcessResponse(BaseClinicalContract):
    text_content: str = Field(..., description="Extracted OCR text content")
    page_count: int = Field(default=1, description="Total pages processed")
    bounding_boxes: List[Dict[str, Any]] = Field(default=[], description="Spatial bounding boxes")

# 3. Extraction Agent (/extract)
class ExtractRequest(BaseClinicalContract):
    file_path: str = Field(..., description="File path to OCR/processed document")
    text_content: Optional[str] = Field(default=None, description="OCR text content")

class ExtractResponse(BaseClinicalContract):
    medications: List[Dict[str, Any]] = Field(default=[], description="Extracted medication items")
    diagnoses: List[Dict[str, Any]] = Field(default=[], description="Extracted diagnosis items")
    labs: List[Dict[str, Any]] = Field(default=[], description="Extracted lab result items")
    confidence_score: float = Field(default=1.0, description="Extraction confidence score")

# 4. Patient Identity Service (/identity/resolve)
class IdentityResolveRequest(BaseClinicalContract):
    raw_demographics: Dict[str, Any] = Field(..., description="Raw patient demographic fields")

class IdentityResolveResponse(BaseClinicalContract):
    patient_id: str = Field(..., description="Resolved master patient identifier")
    match_confidence: float = Field(default=1.0, description="Identity resolution confidence")
    is_quarantined: bool = Field(default=False, description="Flag indicating if identity resolution requires review")

# 5. Terminology Service (/terminology/map)
class TerminologyMapRequest(BaseClinicalContract):
    source_term: str = Field(..., description="Clinical term string")
    source_code: Optional[str] = Field(default=None, description="Source code")
    target_system: str = Field(..., description="Target vocabulary standard (RxNorm, LOINC, ICD-10-CM)")

class TerminologyMapResponse(BaseClinicalContract):
    mapped_code: str = Field(..., description="Mapped standard code")
    system: str = Field(..., description="Vocabulary system URI")
    display_name: str = Field(..., description="Official standard display name")

# 6. Schema Validator (/validate/schema)
class SchemaValidateRequest(BaseClinicalContract):
    clinical_data: Dict[str, Any] = Field(..., description="Clinical data payload")

class SchemaValidateResponse(BaseClinicalContract):
    is_valid: bool = Field(..., description="Validation status boolean")
    issues: List[Dict[str, Any]] = Field(default=[], description="List of schema validation issues")
    requires_manual_review: bool = Field(default=False, description="Manual review requirement flag")

# 7. Clinical Rules Engine (/cql/evaluate)
class CqlEvaluateRequest(BaseClinicalContract):
    patient_id: str = Field(..., description="Target patient identifier")
    cql_library: str = Field(..., description="Name of CQL library to evaluate")

class CqlEvaluateResponse(BaseClinicalContract):
    evaluated_rules: List[Dict[str, Any]] = Field(default=[], description="Evaluated CQL rule results")
    care_gaps_identified: List[Dict[str, Any]] = Field(default=[], description="Care gaps triggered by CQL")

# 8. Temporal Reasoning Engine (/temporal/evaluate)
class TemporalEvaluateRequest(BaseClinicalContract):
    patient_id: str = Field(..., description="Target patient identifier")
    encounter_history: List[Dict[str, Any]] = Field(default=[], description="Historical encounter timeline")

class TemporalEvaluateResponse(BaseClinicalContract):
    overdue_screenings: List[Dict[str, Any]] = Field(default=[], description="Screenings overdue per temporal guidelines")
    timeline_gaps: List[Dict[str, Any]] = Field(default=[], description="Timeline gaps identified")

# 9. Drug Interaction Service (/interactions/check)
class InteractionsCheckRequest(BaseClinicalContract):
    medication_codes: List[str] = Field(..., description="List of RxNorm medication codes")

class InteractionsCheckResponse(BaseClinicalContract):
    interactions_found: List[Dict[str, Any]] = Field(default=[], description="List of identified drug interactions")
    severity_max: str = Field(default="NONE", description="Maximum severity level")

# 10. Guideline Retrieval Service (/guidelines/retrieve)
class GuidelineRetrieveRequest(BaseClinicalContract):
    condition_code: str = Field(..., description="ICD-10 or SNOMED condition code")
    query_text: Optional[str] = Field(default=None, description="Free-text clinical search query")

class GuidelineRetrieveResponse(BaseClinicalContract):
    guidelines: List[Dict[str, Any]] = Field(default=[], description="Retrieved evidence-based guideline passages")

# 11. Safety Sub-Agent (/safety/evaluate)
class SafetyEvaluateRequest(BaseClinicalContract):
    patient_id: str = Field(..., description="Target patient identifier")
    vitals_and_symptoms: Dict[str, Any] = Field(..., description="Extracted vitals and symptoms")

class SafetyEvaluateResponse(BaseClinicalContract):
    is_emergency: bool = Field(default=False, description="Emergency red-flag flag")
    trigger_reason: Optional[str] = Field(default=None, description="Emergency trigger description")
    safety_interrupt: bool = Field(default=False, description="Immediate workflow safety interrupt flag")

# 12. Care Gap Explanation Agent (/care-gap/explain)
class CareGapExplainRequest(BaseClinicalContract):
    patient_id: str = Field(..., description="Patient ID")
    raw_care_gaps: List[Dict[str, Any]] = Field(..., description="Unformatted care gaps")
    guideline_evidence: List[Dict[str, Any]] = Field(..., description="Supporting guideline evidence")

class CareGapExplainResponse(BaseClinicalContract):
    explained_care_gaps: List[Dict[str, Any]] = Field(..., description="Formatted care gap explanations")

# 13. Referral Drafting Agent (/referral/draft)
class ReferralDraftRequest(BaseClinicalContract):
    patient_id: str = Field(..., description="Target patient identifier")
    specialty: str = Field(..., description="Target medical specialty")
    urgency: str = Field(default="ROUTINE", description="Urgency level")
    clinical_reasons: List[str] = Field(default=[], description="Reasons for referral")
    guideline_citations: List[Dict[str, Any]] = Field(default=[], description="Guideline evidence citations")

class ReferralDraftResponse(BaseClinicalContract):
    referral_letter_text: str = Field(..., description="Drafted formal clinical referral letter text")

# 14. Guardrail Service (/guardrail/verify-grounding)
class GuardrailVerifyRequest(BaseClinicalContract):
    draft_text: str = Field(..., description="Generated text to verify")
    source_documents: List[str] = Field(..., description="Authoritative ground-truth text passages")

class GuardrailVerifyResponse(BaseClinicalContract):
    is_grounded: bool = Field(..., description="Grounding verification boolean")
    confidence_score: float = Field(default=1.0, description="Grounding confidence score")
    hallucinated_claims: List[str] = Field(default=[], description="List of ungrounded claims")

# 15. FHIR Integration Service (/fhir/write-transaction)
class FhirWriteTransactionRequest(BaseClinicalContract):
    patient_id: str = Field(..., description="Patient ID")
    fhir_resources: List[Dict[str, Any]] = Field(..., description="List of FHIR resources to write")

class FhirWriteTransactionResponse(BaseClinicalContract):
    status: str = Field(..., description="Transaction status (persisted, duplicate_skipped)")
    fhir_bundle_id: str = Field(..., description="FHIR Transaction Bundle ID")
    is_duplicate: bool = Field(default=False, description="Idempotency deduplication flag")
    resource_references: List[str] = Field(default=[], description="Created resource URIs")

# 16. Audit Service (/audit/events)
class AuditEventRequest(BaseClinicalContract):
    service_name: str = Field(..., description="Originating service name")
    event_type: str = Field(..., description="Audit event classification")
    payload: Dict[str, Any] = Field(..., description="Event payload dictionary")

class AuditEventResponse(BaseClinicalContract):
    status: str = Field(default="recorded", description="Audit event recording status")
    event_id: str = Field(..., description="Unique audit event ID")
    entry_hash: str = Field(..., description="SHA-256 hash of record")
    hmac_signature: str = Field(..., description="HMAC signature of record")

# 17. IAM Service (/iam/auth/login)
class IamLoginRequest(BaseModel):
    username: str = Field(..., description="User login handle")
    password: str = Field(..., description="User password")

class IamLoginResponse(BaseModel):
    access_token: str = Field(..., description="OIDC Access Token string")
    token_type: str = Field(default="bearer", description="Authorization bearer format")
    expires_in_seconds: int = Field(default=900, description="Token expiration in seconds")
    role: str = Field(..., description="Assigned primary role")
    scopes: List[str] = Field(default=[], description="Granted RBAC scopes")
