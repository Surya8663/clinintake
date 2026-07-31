from typing import Any

from pydantic import BaseModel, Field


class GroundedField(BaseModel):
    value: str = Field(..., description="Extracted field value, or 'Incomplete' if confidence < threshold")
    literal_quote: str = Field(..., description="Literal source text snippet extracted from OCR")
    bbox: list[int] = Field(default_factory=list, description="Spatial bounding box [x_min, y_min, x_max, y_max]")
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
    diagnoses: list[GroundedDiagnosis] = []
    medications: list[GroundedMedication] = []
    labs: list[GroundedLabResult] = []

class ExtractRequest(BaseModel):
    document_id: str
    ocr_text: str | None = None
    ocr_words: list[dict[str, Any]] | None = None

class ExtractResponse(BaseModel):
    document_id: str
    extracted_data: ExtractionData
    fhir_resources: list[dict[str, Any]] = Field(default_factory=list, description="Validated FHIR R4 JSON resources")
    overall_confidence: float
    safety_interrupt_triggered: bool = Field(False, description="True if emergency safety interrupt lane was triggered")
    safety_response: dict[str, Any] | None = Field(None, description="Direct Safety Sub-Agent evaluation result")
    safety_interrupt_latency_ms: float | None = Field(None, description="Direct Safety interrupt call latency in ms (< 2000ms SLA)")
