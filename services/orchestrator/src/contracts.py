from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

# General metadata container
class PatientMetadata(BaseModel):
    patient_id: str = Field(..., description="Unique Patient Identifier (valid patient identifier required)")
    first_name: str
    last_name: str
    date_of_birth: str

# 1. Sanitization Agent Contracts
class SanitizeRequest(BaseModel):
    document_id: str
    raw_file_path: str

class SanitizeResponse(BaseModel):
    document_id: str
    sanitized_file_path: Optional[str] = None
    is_safe: bool
    quarantine_reason: Optional[str] = None

# 2. Extraction Agent Contracts
class ClinicalMedication(BaseModel):
    name: str
    rxnorm_code: str = Field(..., description="Standardized RxNorm code")
    dosage: str
    frequency: str

class ClinicalDiagnosis(BaseModel):
    name: str
    icd10_code: str = Field(..., description="Standardized ICD-10-CM code")
    confidence: float

class ClinicalLabResult(BaseModel):
    name: str
    loinc_code: str = Field(..., description="Standardized LOINC code")
    value: str
    unit: str

class ExtractedClinicalData(BaseModel):
    medications: List[ClinicalMedication] = []
    diagnoses: List[ClinicalDiagnosis] = []
    labs: List[ClinicalLabResult] = []

class ExtractRequest(BaseModel):
    document_id: str
    file_path: str

class ExtractResponse(BaseModel):
    document_id: str
    patient_metadata: Optional[PatientMetadata] = None
    extracted_data: ExtractedClinicalData
    confidence_score: float

# 3. Validation Agent Contracts
class ValidateRequest(BaseModel):
    document_id: str
    patient_metadata: PatientMetadata
    extracted_data: ExtractedClinicalData

class ValidationIssue(BaseModel):
    field: str
    issue_type: str  # e.g., "invalid_code", "missing_required"
    description: str
    severity: str  # "warning" or "error"

class ValidateResponse(BaseModel):
    document_id: str
    is_valid: bool
    issues: List[ValidationIssue] = []
    requires_manual_review: bool

# 4. Reasoning Agent Contracts
class CareGap(BaseModel):
    gap_name: str
    status: str  # e.g., "open", "closed"
    evidence: str
    suggested_action: str

class ReasonRequest(BaseModel):
    document_id: str
    patient_id: str
    clinical_data: ExtractedClinicalData

class ReasonResponse(BaseModel):
    document_id: str
    care_gaps: List[CareGap] = []
    requires_human_approval: bool
    reasoning_summary: str

# 5. EHR Writer Contracts
class EHRWriteRequest(BaseModel):
    document_id: str
    patient_id: str
    clinical_data: ExtractedClinicalData
    care_gaps: List[CareGap] = []

class EHRWriteResponse(BaseModel):
    document_id: str
    success: bool
    fhir_resource_ids: List[str] = []
    error_message: Optional[str] = None
