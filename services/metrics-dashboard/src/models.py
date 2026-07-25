from pydantic import BaseModel, Field

class ExtractionAccuracyMetric(BaseModel):
    total_test_samples: int
    correct_fields: int
    total_fields: int
    accuracy_percentage: float = Field(..., description="Extraction accuracy computed against labeled test set")

class RedFlagSensitivityMetric(BaseModel):
    total_emergency_cases: int
    detected_cases: int
    sensitivity_percentage: float = Field(..., description="Red-flag emergency sensitivity computed against benchmark cases")

class HallucinationRateMetric(BaseModel):
    total_explanations: int
    hallucinated_citations: int
    hallucination_rate_percentage: float = Field(..., description="Hallucination rate computed from quote-grounding checks")

class KPISummaryResponse(BaseModel):
    extraction_accuracy: ExtractionAccuracyMetric
    red_flag_sensitivity: RedFlagSensitivityMetric
    hallucination_rate: HallucinationRateMetric
    evaluated_at: str
