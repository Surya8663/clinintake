from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class FailureEnqueueRequest(BaseModel):
    document_id: str
    service_name: str
    error_type: str = Field(..., description="'LOW_CONFIDENCE_EXTRACTION', 'SERVICE_EXCEPTION', 'CLINICIAN_REJECTION'")
    error_message: str
    payload: Dict[str, Any] = Field(default_factory=dict)

class FailureItemResponse(BaseModel):
    document_id: str
    service_name: str
    error_type: str
    error_message: str
    retry_count: int
    max_retries: int
    status: str = Field(..., description="'queued', 'retrying', 'manual_review'")
    enqueued_at: str

class DLQSummaryResponse(BaseModel):
    total_items: int
    manual_review_items: int
    items: List[FailureItemResponse]
