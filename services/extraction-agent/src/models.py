from typing import Any, List, Optional

from pydantic import BaseModel, Field, field_validator


class LyzrFieldResponse(BaseModel):
    value: str = Field(...)
    literal_quote: str = Field(...)
    confidence: float = Field(...)

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        if not isinstance(v, (int, float)) or not (0.0 <= float(v) <= 1.0):
            raise ValueError(f"Confidence score {v} must be a finite float between 0.0 and 1.0")
        return float(v)


class LyzrDiagnosisResponse(BaseModel):
    name: LyzrFieldResponse
    icd10_code: LyzrFieldResponse


class LyzrMedicationResponse(BaseModel):
    name: LyzrFieldResponse
    rxnorm_code: LyzrFieldResponse
    dosage: LyzrFieldResponse


class LyzrLabResponse(BaseModel):
    name: LyzrFieldResponse
    loinc_code: LyzrFieldResponse
    value: LyzrFieldResponse


class LyzrExtractionResponse(BaseModel):
    patient_id: LyzrFieldResponse
    diagnoses: List[LyzrDiagnosisResponse] = Field(default_factory=list)
    medications: List[LyzrMedicationResponse] = Field(default_factory=list)
    labs: List[LyzrLabResponse] = Field(default_factory=list)


class GroundedField(BaseModel):
    value: str = Field(..., description="Extracted field value, or 'Incomplete' if confidence < threshold")
    literal_quote: str = Field(..., description="Literal source text snippet extracted from OCR")
    bbox: Optional[List[int]] = Field(default=None, description="Spatial bounding box [x_min, y_min, x_max, y_max] or None if unavailable")
    grounding_status: str = Field(default="grounded", description="'grounded', 'spatial_data_unavailable', 'quote_not_located', 'quote_unsupported'")
    confidence: float = Field(..., description="Field confidence score between 0.0 and 1.0")


class GroundedDiagnosis(BaseModel):
    name: GroundedField
    icd10_code: GroundedField


class GroundedMedication(BaseModel):
    name: GroundedField
    rxnorm_code: GroundedField
    dosage: GroundedField


class GroundedLabResult(BaseModel):
    name: GroundedField
    loinc_code: GroundedField
    value: GroundedField


class ExtractionData(BaseModel):
    patient_id: GroundedField
    diagnoses: List[GroundedDiagnosis] = Field(default_factory=list)
    medications: List[GroundedMedication] = Field(default_factory=list)
    labs: List[GroundedLabResult] = Field(default_factory=list)


class ExtractRequest(BaseModel):
    document_id: str
    ocr_text: Optional[str] = None
    ocr_words: Optional[List[dict[str, Any]]] = None


class ExtractResponse(BaseModel):
    document_id: str
    extracted_data: ExtractionData
    fhir_resources: List[dict[str, Any]] = Field(default_factory=list, description="Validated FHIR R4 JSON resources")
    overall_confidence: float
    safety_interrupt_triggered: bool = Field(False, description="True if emergency safety interrupt lane was triggered")
    safety_response: Optional[dict[str, Any]] = Field(None, description="Direct Safety Sub-Agent evaluation result")
    safety_interrupt_latency_ms: Optional[float] = Field(None, description="Direct Safety interrupt call latency in ms (< 2000ms SLA)")
