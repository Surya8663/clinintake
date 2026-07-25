from pydantic import BaseModel, Field
from typing import Optional

class TerminologyMapRequest(BaseModel):
    term: str = Field(..., description="Raw clinical term to normalize (e.g. 'Lisinopril 10mg', 'HbA1c')")
    code_system: str = Field("RxNorm", description="Target system: 'RxNorm', 'LOINC', 'SNOMED'")

class TerminologyMapResponse(BaseModel):
    raw_term: str
    code_system: str
    code: Optional[str] = Field(None, description="Mapped code (e.g. RxCUI, LOINC num, SNOMED ID)")
    display_name: Optional[str] = Field(None, description="Official system concept display name")
    confidence_score: float = Field(..., description="Confidence score between 0.0 and 1.0")
    is_mapped: bool = Field(..., description="True if mapped with confidence >= threshold")
    requires_unmapped_escalation: bool = Field(..., description="True if concept could not be mapped reliably")
    source_api: str = Field(..., description="API or index used for mapping (e.g., NLM_RxNav, SNOMED_CT_Index)")
