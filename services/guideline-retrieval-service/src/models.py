from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class GuidelineChunk(BaseModel):
    chunk_id: str
    text: str = Field(..., description="Published USPSTF guideline passage text")
    source: str = Field(..., description="Guideline publisher (e.g. 'USPSTF', 'ADA', 'ACC/AHA')")
    version: str = Field(..., description="Guideline version identifier (e.g. '2021-V1', '2024-V2')")
    effective_date: str = Field(..., description="Effective date (YYYY-MM-DD)")
    section: str = Field(..., description="Guideline section header")
    clause_id: str = Field(..., description="Clause / recommendation ID")

class GuidelineQueryRequest(BaseModel):
    query: str = Field(..., description="Clinical query / patient condition context")
    min_relevance_score: Optional[float] = Field(None, description="Relevance score threshold (defaults to 0.60)")
    metadata_filter: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Metadata key-value filters (e.g. {'source': 'USPSTF'})")

class GuidelineMatch(BaseModel):
    passage: str
    source: str
    version: str
    effective_date: str
    section: str
    clause_id: str
    similarity_score: float

class GuidelineQueryResponse(BaseModel):
    query: str
    status: str = Field(..., description="'success' or 'insufficient_guideline_evidence'")
    matches: List[GuidelineMatch] = Field(default_factory=list)
    relevance_threshold_used: float
