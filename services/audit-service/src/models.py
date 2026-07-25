from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class AuditEventCreate(BaseModel):
    event_id: Optional[str] = None
    document_id: str
    service_name: str
    event_type: str = Field(..., description="E.g., 'DOCUMENT_INGESTED', 'PII_REDACTED', 'SAFETY_INTERRUPT_TRIGGERED'")
    payload: Dict[str, Any] = Field(default_factory=dict)
    timestamp: Optional[str] = None

class AuditRecordResponse(BaseModel):
    id: int
    event_id: str
    document_id: str
    service_name: str
    event_type: str
    payload: Dict[str, Any]
    prev_hash: str
    entry_hash: str
    hmac_signature: str
    created_at: str

class AuditQueryResponse(BaseModel):
    total_records: int
    records: List[AuditRecordResponse]

class IntegrityVerifyResponse(BaseModel):
    status: str = Field(..., description="'intact' or 'compromised'")
    total_verified: int
    failed_entry_id: Optional[int] = None
    details: str
