from pydantic import BaseModel, Field


class TemporalEvaluateRequest(BaseModel):
    procedure_name: str = Field(..., description="Screening procedure name (e.g. 'Colonoscopy', 'HbA1c_Testing', 'Mammogram')")
    last_screening_date: str | None = Field(None, description="ISO format date YYYY-MM-DD or None if missing")
    patient_age: int | None = Field(None, description="Patient age in years")
    risk_category: str = Field("average", description="Risk category: 'average', 'high', 'very_high'")
    guideline_interval_months: int = Field(12, description="Recommended screening interval in months")
    reference_date: str | None = Field(None, description="Current evaluation date override (YYYY-MM-DD) for testing")


class TemporalEvaluateResponse(BaseModel):
    procedure_name: str
    status: str = Field(..., description="'due', 'overdue', 'not-due', or 'insufficient-information'")
    months_since_last_screening: float | None = None
    next_due_date: str | None = None
    rationale: str
