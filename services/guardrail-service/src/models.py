from typing import Any

from pydantic import BaseModel, Field


class GroundingVerificationRequest(BaseModel):
    generated_text: str = Field(..., description="LLM generated clinical claim or text output")
    source_evidence_spans: list[Any] = Field(default_factory=list, description="Ground-truth quotes or evidence spans")
    guideline_passages: list[Any] = Field(default_factory=list, description="Ground-truth retrieved guideline passages")


class GroundingVerificationResponse(BaseModel):
    is_safe: bool
    blocked: bool = Field(..., description="True if response MUST be blocked due to hallucination")
    grounding_score: float = Field(..., description="Score 0.0 - 1.0 representing citation grounding overlap")
    hallucinated_claims: list[str] = Field(default_factory=list)
    reason: str


class PHIScrubRequest(BaseModel):
    raw_text: str


class PHIScrubResponse(BaseModel):
    scrubbed_text: str
    entities_redacted_count: int
    redacted_types: list[str] = Field(default_factory=list)
