from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class LyzrFieldResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    value: str = Field(...)
    literal_quote: str = Field(...)
    confidence: float = Field(...)

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        if not isinstance(v, (int, float)) or not (0.0 <= float(v) <= 1.0):
            raise ValueError(f"Confidence score {v} must be a finite float between 0.0 and 1.0")
        return float(v)

    @field_validator("value")
    @classmethod
    def validate_value_string(cls, v: str) -> str:
        if v.strip() in ("Unknown", "Incomplete"):
            raise ValueError(f"Lyzr external response contains forbidden fallback string '{v}'")
        return v

    @model_validator(mode="after")
    def validate_field_consistency(self) -> "LyzrFieldResponse":
        val_clean = self.value.strip()
        quote_clean = self.literal_quote.strip()

        # If value is non-empty and supported, literal_quote MUST be non-empty
        if val_clean:
            if not quote_clean:
                raise ValueError(f"Supported value '{self.value}' missing required verbatim literal_quote")
        else:
            # If value is empty, confidence MUST be 0.0
            if self.confidence != 0.0:
                raise ValueError(f"Empty value must have confidence 0.0, got {self.confidence}")

        return self


class LyzrDiagnosisResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: LyzrFieldResponse
    icd10_code: LyzrFieldResponse


class LyzrMedicationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: LyzrFieldResponse
    rxnorm_code: LyzrFieldResponse
    dosage: LyzrFieldResponse


class LyzrLabResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: LyzrFieldResponse
    loinc_code: LyzrFieldResponse
    value: LyzrFieldResponse


class LyzrExtractionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    patient_id: LyzrFieldResponse
    diagnoses: List[LyzrDiagnosisResponse] = Field(default_factory=list)
    medications: List[LyzrMedicationResponse] = Field(default_factory=list)
    labs: List[LyzrLabResponse] = Field(default_factory=list)


class OCRBoundingBox(BaseModel):
    x_min: float = Field(...)
    y_min: float = Field(...)
    x_max: float = Field(...)
    y_max: float = Field(...)

    @model_validator(mode="after")
    def validate_coordinates(self) -> "OCRBoundingBox":
        if self.x_min < 0 or self.y_min < 0 or self.x_max < 0 or self.y_max < 0:
            raise ValueError("Bounding box coordinates must be non-negative")
        if self.x_max <= self.x_min or self.y_max <= self.y_min:
            raise ValueError(f"Invalid bounding box dimensions: x_max ({self.x_max}) must be > x_min ({self.x_min}) and y_max ({self.y_max}) must be > y_min ({self.y_min})")
        return self


class OCRWord(BaseModel):
    text: str = Field(...)
    bbox: Optional[dict[str, Any]] = None


class GroundedField(BaseModel):
    value: str = Field(..., description="Extracted field value, or 'Incomplete' if confidence < threshold")
    literal_quote: str = Field(..., description="Literal source text snippet extracted from OCR")
    bbox: Optional[List[float]] = Field(default=None, description="Spatial bounding box [x_min, y_min, x_max, y_max] or None if invalid/unavailable")
    grounding_status: str = Field(default="grounded", description="'grounded', 'spatial_data_unavailable', 'spatial_data_invalid', 'quote_not_located', 'quote_unsupported'")
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
