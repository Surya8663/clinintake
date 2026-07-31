from typing import Any

from pydantic import BaseModel, Field


class AuditEventCreate(BaseModel):
    event_id: str | None = None
    document_id: str
    service_name: str
    event_type: str = Field(..., description="E.g., 'DOCUMENT_INGESTED', 'PII_REDACTED', 'SAFETY_INTERRUPT_TRIGGERED'")
    payload: dict[str, Any] = Field(default_factory=dict)
    timestamp: str | None = None

class AuditRecordResponse(BaseModel):
    id: int
    event_id: str
    document_id: str
    service_name: str
    event_type: str
    payload: dict[str, Any]
    prev_hash: str
    entry_hash: str
    hmac_signature: str
    created_at: str

class AuditQueryResponse(BaseModel):
    total_records: int
    records: list[AuditRecordResponse]

class IntegrityVerifyResponse(BaseModel):
    status: str = Field(..., description="'intact' or 'compromised'")
    total_verified: int
    failed_entry_id: int | None = None
    details: str
