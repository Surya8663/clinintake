from typing import Any

from pydantic import BaseModel, Field


class ReferralDraftRequest(BaseModel):
    document_id: str
    patient_id: str | None = None
    target_specialty: str | None = Field("Gastroenterology", description="Specialty targeted for referral")
    clinical_decision_package: dict[str, Any] = Field(default_factory=dict, description="Structured Clinical Decision Package")


class GroundedEvidenceItem(BaseModel):
    source_quote: str
    section: str
    clause_id: str | None = None


class ReferralDraftResponse(BaseModel):
    document_id: str
    patient_id: str | None
    target_specialty: str
    urgency_level: str = Field("ROUTINE", description="'ROUTINE', 'URGENT', 'EMERGENCY'")
    referral_letter_text: str = Field(..., description="Draft clinical referral letter text")
    clinical_reasons: list[str] = Field(default_factory=list)
    grounded_evidence: list[GroundedEvidenceItem] = Field(default_factory=list)
