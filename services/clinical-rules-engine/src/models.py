from typing import Any

from pydantic import BaseModel, Field


class CQLRuleResult(BaseModel):
    rule_name: str
    is_satisfied: bool
    rationale: str
    matched_codes: list[str] = Field(default_factory=list)


class CQLEvaluateRequest(BaseModel):
    patient_id: str
    clinical_data: dict[str, Any] = Field(..., description="Extracted clinical conditions, medications, labs")
    rule_library: list[str] | None = Field(default=["Diabetes_Screening", "Hypertension_Control", "Colorectal_Screening"], description="CQL Rule sets to evaluate")


class CQLEvaluateResponse(BaseModel):
    patient_id: str
    is_eligible: bool
    evaluated_rules: list[CQLRuleResult]
    inclusion_criteria_met: list[str]
    exclusion_criteria_met: list[str]
