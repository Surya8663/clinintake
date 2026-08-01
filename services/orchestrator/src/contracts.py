from packages.clinical_contracts import (
    BaseClinicalContract,
    CareGapExplainRequest,
    CareGapExplainResponse,
    FhirWriteTransactionRequest,
    FhirWriteTransactionResponse,
    FilterScanRequest,
    FilterScanResponse,
    SchemaValidateRequest,
    SchemaValidateResponse,
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
