from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class ReferralDraftRequest(BaseModel):
    document_id: str
    patient_id: Optional[str] = None
    target_specialty: Optional[str] = Field("Gastroenterology", description="Specialty targeted for referral")
    clinical_decision_package: Dict[str, Any] = Field(default_factory=dict, description="Structured Clinical Decision Package")

class GroundedEvidenceItem(BaseModel):
    source_quote: str
    section: str
    clause_id: Optional[str] = None

class ReferralDraftResponse(BaseModel):
    document_id: str
    patient_id: Optional[str]
    target_specialty: str
    urgency_level: str = Field("ROUTINE", description="'ROUTINE', 'URGENT', 'EMERGENCY'")
    referral_letter_text: str = Field(..., description="Draft clinical referral letter text")
    clinical_reasons: List[str] = Field(default_factory=list)
    grounded_evidence: List[GroundedEvidenceItem] = Field(default_factory=list)
