from pydantic import BaseModel, Field


class AlertDispatchRequest(BaseModel):
    document_id: str
    patient_id: str | None = None
    severity: str = Field("EMERGENCY", description="'EMERGENCY', 'CRITICAL', 'WARNING'")
    channels: list[str] = Field(default_factory=lambda: ["SMS", "EMAIL", "WEBHOOK"])
    alert_message: str


class ChannelDispatchStatus(BaseModel):
    channel: str
    status: str = Field("SENT", description="'SENT', 'FAILED'")
    target_destination: str


class AlertDispatchResponse(BaseModel):
    document_id: str
    severity: str
    dispatched_channels: list[ChannelDispatchStatus] = Field(default_factory=list)
    dispatch_latency_ms: float = Field(..., description="Latency measurement in ms (< 2000ms SLA)")
    sla_met: bool = Field(True, description="True if dispatch latency < 2.0s SLA requirement")
