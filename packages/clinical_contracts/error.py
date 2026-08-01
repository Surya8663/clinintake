from pydantic import BaseModel, Field


class ApiErrorEnvelope(BaseModel):
    """
    Standardized, machine-readable inter-service error envelope.
    Contains zero PHI/PII data.
    """

    schema_version: str = Field(default="2.0.0", description="Contract schema version")
    code: str = Field(..., description="Machine-readable error code (e.g. INVALID_DOCUMENT_ID, DOWNSTREAM_TIMEOUT)")
    message: str = Field(..., description="Safe, non-PHI error summary for logging and UI error display")
    retryable: bool = Field(default=False, description="Indicates if operation is safe to retry")
    dependency: str | None = Field(default=None, description="Name of upstream/downstream service where failure occurred")
    trace_id: str | None = Field(default=None, description="Distributed trace ID for correlation")
    document_id: str | None = Field(default=None, description="Clinical document identifier")
