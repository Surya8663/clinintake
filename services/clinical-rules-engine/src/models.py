from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class CQLRuleResult(BaseModel):
    rule_name: str
    is_satisfied: bool
    rationale: str
    matched_codes: List[str] = Field(default_factory=list)

class CQLEvaluateRequest(BaseModel):
    patient_id: str
    clinical_data: Dict[str, Any] = Field(..., description="Extracted clinical conditions, medications, labs")
    rule_library: Optional[List[str]] = Field(default=["Diabetes_Screening", "Hypertension_Control", "Colorectal_Screening"], description="CQL Rule sets to evaluate")

class CQLEvaluateResponse(BaseModel):
    patient_id: str
    is_eligible: bool
    evaluated_rules: List[CQLRuleResult]
    inclusion_criteria_met: List[str]
    exclusion_criteria_met: List[str]
