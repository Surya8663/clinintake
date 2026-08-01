from pydantic import BaseModel, Field


class VitalsMeasurement(BaseModel):
    respiratory_rate: int | None = Field(None, description="Breaths per minute (normal 12-20)")
    spo2: float | None = Field(None, description="Oxygen saturation percentage (normal 96-100%)")
    uses_supplemental_oxygen: bool | None = Field(False, description="True if patient requires oxygen therapy")
    systolic_bp: int | None = Field(None, description="Systolic blood pressure mmHg (normal 111-219)")
    heart_rate: int | None = Field(None, description="Heart rate / pulse beats per minute (normal 51-90)")
    consciousness_level: str | None = Field(None, description="ACVPU scale: 'Alert', 'Confusion', 'Voice', 'Pain', 'Unresponsive'")
    temperature: float | None = Field(None, description="Body temperature in Celsius (normal 36.1-38.0 C)")


class RedFlagTrigger(BaseModel):
    syndrome: str = Field(..., description="Red-flag category ('sepsis', 'stroke', 'anaphylaxis', 'major_bleeding', 'suicidal_ideation', 'chest_pain', 'severe_respiratory_distress')")
    severity: str = Field(..., description="'EMERGENCY' or 'CRITICAL'")
    description: str = Field(..., description="Clinical rationale for red-flag trigger")
    trigger_source: str = Field(..., description="'NEWS2_Score', 'qSOFA_Criteria', 'Heuristic_RedFlag_Keywords'")


class SafetyEvaluateRequest(BaseModel):
    document_id: str
    patient_id: str | None = None
    vitals: VitalsMeasurement | None = None
    clinical_text: str | None = None
    symptoms: list[str] | None = Field(default_factory=list)


class SafetyEvaluateResponse(BaseModel):
    document_id: str
    is_emergency: bool = Field(..., description="True if immediate emergency safety interrupt lane MUST trigger")
    news2_score: int | None = Field(None, description="Calculated NEWS2 score (0-20)")
    qsofa_score: int | None = Field(None, description="Calculated qSOFA score (0-3)")
    red_flags: list[RedFlagTrigger] = Field(default_factory=list)
    assessment_status: str = Field(..., description="'complete' or 'incomplete'")
    rationale: str = Field(..., description="Detailed clinical assessment rationale")
    latency_ms: float = Field(..., description="Evaluation latency in milliseconds (< 2000ms SLA)")
