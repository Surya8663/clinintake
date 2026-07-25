from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class FHIRTransactionRequest(BaseModel):
    document_id: str
    patient_id: str
    idempotency_key: str = Field(..., description="Unique client idempotency key to prevent duplicate writes")
    fhir_resources: List[Dict[str, Any]] = Field(default_factory=list, description="List of valid FHIR R4 resources to bundle")

class FHIRTransactionResponse(BaseModel):
    document_id: str
    status: str = Field(..., description="'persisted' or 'no_op_duplicate_suppressed'")
    fhir_bundle_id: str
    resource_references: List[str] = Field(default_factory=list, description="URIs of persisted FHIR resources in EHR")
    is_duplicate: bool = Field(False, description="True if transaction was suppressed as duplicate no-op")
    timestamp: str
