from typing import Any, List, Optional

from pydantic import BaseModel, Field


class ClinicalDecisionPackage(BaseModel):
    document_id: str
    patient_id: Optional[str] = None
    rules_evaluations: List[dict[str, Any]] = Field(default_factory=list, description="CQL inclusion/exclusion evaluations")
    temporal_care_gaps: List[dict[str, Any]] = Field(default_factory=list, description="Calculated care gap statuses (due, overdue, etc.)")
    drug_interactions: List[dict[str, Any]] = Field(default_factory=list, description="Drug-drug and drug-allergy interactions")
    safety_assessment: dict[str, Any] = Field(default_factory=dict, description="NEWS2, qSOFA, and red flags")
    guideline_passages: List[dict[str, Any]] = Field(default_factory=list, description="USPSTF retrieved passages with section/clause metadata")


class CitationItem(BaseModel):
    source_title: str
    version: str
    section: str
    clause_id: str
    passage_text: str
    similarity_score: float


class GuidelinePassage(BaseModel):
    clause_id: str
    source: str = ""
    source_title: str = ""
    version: str = ""
    section: str = ""
    passage_text: str = ""
    similarity_score: float = 0.0


class DocumentSpanItem(BaseModel):
    field_name: str
    source_quote: str


class CareGapExplanationResponse(BaseModel):
    document_id: str
    explanation_summary: str = Field(..., description="Grounded natural language clinical care gap explanation")
    care_gaps_found: List[str] = Field(default_factory=list, description="List of specific identified care gaps")
    cited_guideline_passages: List[CitationItem] = Field(default_factory=list, description="Citations directly referenced by verified LLM output")
    document_evidence_spans: List[DocumentSpanItem] = Field(default_factory=list, description="Document evidence spans from package")
    generation_mode: str = Field(default="llm", description="'llm' for LLM-generated explanation, 'insufficient_evidence' for empty guideline evidence")
