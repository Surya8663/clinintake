from typing import Any

from pydantic import BaseModel, Field


class ClinicalDecisionPackage(BaseModel):
    document_id: str
    patient_id: str | None = None
    rules_evaluations: list[dict[str, Any]] = Field(default_factory=list, description="CQL inclusion/exclusion evaluations")
    temporal_care_gaps: list[dict[str, Any]] = Field(default_factory=list, description="Calculated care gap statuses (due, overdue, etc.)")
    drug_interactions: list[dict[str, Any]] = Field(default_factory=list, description="Drug-drug and drug-allergy interactions")
    safety_assessment: dict[str, Any] = Field(default_factory=dict, description="NEWS2, qSOFA, and red flags")
    guideline_passages: list[dict[str, Any]] = Field(default_factory=list, description="USPSTF retrieved passages with section/clause metadata")

class CitationItem(BaseModel):
    source_title: str
    version: str
    section: str
    clause_id: str
    passage_text: str
    similarity_score: float

class DocumentSpanItem(BaseModel):
    field_name: str
    source_quote: str

class CareGapExplanationResponse(BaseModel):
    document_id: str
    explanation_summary: str = Field(..., description="Grounded natural language clinical care gap explanation")
    care_gaps_found: list[str] = Field(default_factory=list, description="List of specific identified care gaps")
    cited_guideline_passages: list[CitationItem] = Field(default_factory=list, description="Citations directly extracted from input package passages")
    document_evidence_spans: list[DocumentSpanItem] = Field(default_factory=list, description="Document evidence spans from package")
    generation_mode: str = Field(default="llm", description="'llm' for LLM-generated, 'deterministic_fallback' if LLM failed and deterministic template was used")
