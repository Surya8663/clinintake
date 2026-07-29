from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class GuidelineChunk(BaseModel):
    chunk_id: str = Field(..., description="Unique chunk identifier")
    guideline_id: str = Field(..., description="Unique guideline identifier (e.g. USPSTF-CRC-2021)")
    source_organization: str = Field(default="USPSTF", description="Publishing organization (USPSTF, ADA, ACC/AHA)")
    title: str = Field(..., description="Guideline title")
    version: str = Field(..., description="Guideline version identifier (e.g. 2021-V1)")
    effective_date: str = Field(..., description="Effective publication date (YYYY-MM-DD)")
    review_or_expiry_date: Optional[str] = Field(default=None, description="Scheduled review or expiry date")
    jurisdiction: str = Field(default="US", description="Target medical jurisdiction (US, EU, UK)")
    section: str = Field(..., description="Guideline section title / recommendation area")
    recommendation_strength: str = Field(default="Grade A", description="USPSTF Recommendation Grade (Grade A, B, C, D, I)")
    population_tags: List[str] = Field(default_factory=list, description="Target patient population tags")
    source_url: Optional[str] = Field(default=None, description="HTTPS URL of official published guideline source")
    document_checksum: str = Field(..., description="SHA-256 checksum of source document")
    chunk_checksum: str = Field(..., description="SHA-256 checksum of chunk text")
    page: int = Field(default=1, description="Source page number")
    text: str = Field(..., description="Exact published recommendation passage text")
    clause_id: str = Field(..., description="Clause / recommendation clause identifier")
    is_active: bool = Field(default=True, description="Flag indicating if guideline chunk is currently active")

class GuidelineQueryRequest(BaseModel):
    query: str = Field(..., description="Clinical query / patient condition context")
    min_relevance_score: Optional[float] = Field(None, description="Relevance score threshold (defaults to 0.60)")
    metadata_filter: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Metadata key-value filters (e.g. {'jurisdiction': 'US'})")

class GuidelineMatch(BaseModel):
    passage: str
    source: str
    version: str
    effective_date: str
    section: str
    clause_id: str
    similarity_score: float
    qdrant_point_id: Optional[str] = None
    fusion_method: Optional[str] = None
    chunk_checksum: Optional[str] = None

class GuidelineQueryResponse(BaseModel):
    query: str
    status: str = Field(..., description="'success' or 'insufficient_guideline_evidence'")
    matches: List[GuidelineMatch] = Field(default_factory=list)
    relevance_threshold_used: float
