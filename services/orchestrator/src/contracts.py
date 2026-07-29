from packages.clinical_contracts import (
    BaseClinicalContract,
    ApiErrorEnvelope,
    ClinicalWorkflowContext,
    FilterScanRequest, FilterScanResponse,
    OcrProcessRequest, OcrProcessResponse,
    ExtractRequest, ExtractResponse,
    IdentityResolveRequest, IdentityResolveResponse,
    TerminologyMapRequest, TerminologyMapResponse,
    SchemaValidateRequest, SchemaValidateResponse,
    CqlEvaluateRequest, CqlEvaluateResponse,
    TemporalEvaluateRequest, TemporalEvaluateResponse,
    InteractionsCheckRequest, InteractionsCheckResponse,
    GuidelineRetrieveRequest, GuidelineRetrieveResponse,
    SafetyEvaluateRequest, SafetyEvaluateResponse,
    CareGapExplainRequest, CareGapExplainResponse,
    ReferralDraftRequest, ReferralDraftResponse,
    GuardrailVerifyRequest, GuardrailVerifyResponse,
    FhirWriteTransactionRequest, FhirWriteTransactionResponse,
    AuditEventRequest, AuditEventResponse,
    IamLoginRequest, IamLoginResponse
)

# Re-export definitions for backwards compatibility
class PatientMetadata(BaseClinicalContract):
    patient_id: str
    first_name: str
    last_name: str
    date_of_birth: str

SanitizeRequest = FilterScanRequest
SanitizeResponse = FilterScanResponse
ValidateRequest = SchemaValidateRequest
ValidateResponse = SchemaValidateResponse
ReasonRequest = CareGapExplainRequest
ReasonResponse = CareGapExplainResponse
EHRWriteRequest = FhirWriteTransactionRequest
EHRWriteResponse = FhirWriteTransactionResponse
