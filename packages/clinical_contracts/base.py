import uuid

from pydantic import BaseModel, Field


class BaseClinicalContract(BaseModel):
    """Base class for all inter-service request and response contracts."""

    schema_version: str = Field(default="2.0.0", description="Contract schema version")
    workflow_id: str | None = Field(default=None, description="Global workflow instance ID")
    document_id: str = Field(..., description="Unique clinical document identifier")
    trace_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Distributed tracing identifier")
    correlation_id: str | None = Field(default=None, description="Audit correlation identifier")
    idempotency_key: str | None = Field(default=None, description="Idempotency key for side-effect operations")
