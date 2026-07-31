
from pydantic import BaseModel, Field


class DrugItem(BaseModel):
    name: str = Field(..., description="Medication name (e.g., 'Lisinopril')")
    rxnorm_code: str | None = Field(None, description="RxNorm RxCUI code if available")

class AllergyItem(BaseModel):
    substance: str = Field(..., description="Allergen name (e.g., 'Penicillin', 'ACE Inhibitors')")
    reaction: str | None = Field(None, description="Allergic reaction type")

class DrugInteraction(BaseModel):
    interaction_type: str = Field(..., description="'drug-drug' or 'drug-allergy'")
    source_item: str
    target_item: str
    severity: str = Field(..., description="'high', 'moderate', 'low'")
    evidence: str = Field(..., description="Literal clinical evidence / description")
    source_database: str = Field(..., description="'NLM_RxNav', 'openFDA', 'Clinical_Rx_Database'")

class InteractionCheckRequest(BaseModel):
    medications: list[DrugItem] = Field(..., description="List of active or proposed medications")
    allergies: list[AllergyItem] = Field(default_factory=list, description="Patient known allergies")

class InteractionCheckResponse(BaseModel):
    has_interactions: bool
    has_high_severity: bool
    interactions: list[DrugInteraction]
    plain_language_explanation: str = Field(..., description="Post-processed plain language explanation of deterministic results")
