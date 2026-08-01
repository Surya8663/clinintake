from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class LyzrEvidenceRefResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    clause_id: Optional[str] = None
    source_quote: str = Field(..., min_length=1)


class LyzrReferralResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    referral_letter_text: str = Field(..., min_length=1)
    evidence_refs_used: List[LyzrEvidenceRefResponse] = Field(default_factory=list)


class ReferralDraftRequest(BaseModel):
    document_id: str = Field(..., min_length=1)
    patient_id: Optional[str] = Field(None, description="Patient identifier — required for referral creation")
    target_specialty: Optional[str] = Field(None, description="Specialty targeted for referral — must be explicitly supplied or deterministically derived")
    clinical_decision_package: dict[str, Any] = Field(default_factory=dict, description="Structured Clinical Decision Package")


class GroundedEvidenceItem(BaseModel):
    source_quote: str = Field(..., min_length=1)
    section: Optional[str] = None
    clause_id: Optional[str] = None

    @model_validator(mode="after")
    def validate_metadata(self) -> "GroundedEvidenceItem":
        sec_clean = (self.section or "").strip()
        clause_clean = (self.clause_id or "").strip()
        if not sec_clean and not clause_clean:
            raise ValueError("GroundedEvidenceItem requires at least one valid metadata attribute (section or clause_id)")
        return self


class ReferralDraftResponse(BaseModel):
    document_id: str
    patient_id: str
    target_specialty: str
    urgency_level: str = Field("ROUTINE", description="'ROUTINE', 'URGENT', 'EMERGENCY'")
    referral_letter_text: str = Field(..., description="Draft clinical referral letter text")
    clinical_reasons: List[str] = Field(default_factory=list)
    grounded_evidence: List[GroundedEvidenceItem] = Field(default_factory=list)
