from fastapi import FastAPI, HTTPException

from src.config import settings
from src.logger import logger
from src.models import AlertDispatchRequest, AlertDispatchResponse
from src.alert_dispatcher import dispatch_multi_channel_alerts

app = FastAPI(
    title=settings.service_name,
    description="Multi-Channel Safety Alerting & SLA Latency Dispatcher",
    version="1.0.0"
)

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": settings.service_name,
        "sla_threshold_ms": settings.sla_latency_threshold_ms
    }

@app.post("/notify/alert", response_model=AlertDispatchResponse)
async def send_critical_alert(request: AlertDispatchRequest):
    """Dispatches critical safety emergency notifications with real sub-2.0 second SLA latency tracking."""
    logger.info(f"Received alert request for document_id={request.document_id}")
    if not request.document_id:
        raise HTTPException(status_code=400, detail="document_id must be provided")

    response = await dispatch_multi_channel_alerts(request)
    return response
