from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class ReviewItem(BaseModel):
    document_id: str
    patient_id: str
    status: str = Field(..., description="'awaiting_approval', 'approved', 'rejected'")
    created_at: str

class EvidenceSpan(BaseModel):
    field_name: str
    source_quote: str
    bbox: List[int] = Field(default_factory=list, description="[x_min, y_min, x_max, y_max]")

class DocumentFindingsResponse(BaseModel):
    document_id: str
    patient_id: str
    referral_text: str
    evidence_spans: List[EvidenceSpan] = Field(default_factory=list)
    status: str

class ReferralEditRequest(BaseModel):
    edited_referral_text: str

class DecisionSubmitRequest(BaseModel):
    decision: str = Field(..., description="'APPROVED' or 'REJECTED'")
    clinician_id: Optional[str] = Field(None, description="NPI / Clinician ID")
    digital_signature: str = Field(..., description="Cryptographic digital signature string")
    notes: Optional[str] = None

class DecisionSubmitResponse(BaseModel):
    document_id: str
    decision: str
    status: str
    signed_event_emitted: bool
    message: str
