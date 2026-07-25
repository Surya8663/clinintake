from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class VitalsMeasurement(BaseModel):
    respiratory_rate: Optional[int] = Field(None, description="Breaths per minute (normal 12-20)")
    spo2: Optional[float] = Field(None, description="Oxygen saturation percentage (normal 96-100%)")
    uses_supplemental_oxygen: Optional[bool] = Field(False, description="True if patient requires oxygen therapy")
    systolic_bp: Optional[int] = Field(None, description="Systolic blood pressure mmHg (normal 111-219)")
    heart_rate: Optional[int] = Field(None, description="Heart rate / pulse beats per minute (normal 51-90)")
    consciousness_level: Optional[str] = Field(None, description="ACVPU scale: 'Alert', 'Confusion', 'Voice', 'Pain', 'Unresponsive'")
    temperature: Optional[float] = Field(None, description="Body temperature in Celsius (normal 36.1-38.0 C)")

class RedFlagTrigger(BaseModel):
    syndrome: str = Field(..., description="Red-flag category ('sepsis', 'stroke', 'anaphylaxis', 'major_bleeding', 'suicidal_ideation', 'chest_pain', 'severe_respiratory_distress')")
    severity: str = Field(..., description="'EMERGENCY' or 'CRITICAL'")
    description: str = Field(..., description="Clinical rationale for red-flag trigger")
    trigger_source: str = Field(..., description="'NEWS2_Score', 'qSOFA_Criteria', 'Heuristic_RedFlag_Keywords'")

class SafetyEvaluateRequest(BaseModel):
    document_id: str
    patient_id: Optional[str] = None
    vitals: Optional[VitalsMeasurement] = None
    clinical_text: Optional[str] = None
    symptoms: Optional[List[str]] = Field(default_factory=list)

class SafetyEvaluateResponse(BaseModel):
    document_id: str
    is_emergency: bool = Field(..., description="True if immediate emergency safety interrupt lane MUST trigger")
    news2_score: Optional[int] = Field(None, description="Calculated NEWS2 score (0-20)")
    qsofa_score: Optional[int] = Field(None, description="Calculated qSOFA score (0-3)")
    red_flags: List[RedFlagTrigger] = Field(default_factory=list)
    assessment_status: str = Field(..., description="'complete' or 'incomplete'")
    rationale: str = Field(..., description="Detailed clinical assessment rationale")
    latency_ms: float = Field(..., description="Evaluation latency in milliseconds (< 2000ms SLA)")
