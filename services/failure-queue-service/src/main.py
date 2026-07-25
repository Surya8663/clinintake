from fastapi import FastAPI, HTTPException

from src.config import settings
from src.logger import logger
from src.models import FailureEnqueueRequest, FailureItemResponse, DLQSummaryResponse
from src.dlq_engine import enqueue_failure_item, execute_retry, list_dlq_items

app = FastAPI(
    title=settings.service_name,
    description="Dead-Letter Queue with Retry Tracking and Manual Escalation",
    version="1.0.0"
)

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": settings.service_name,
        "max_retries": settings.max_retries
    }

@app.post("/failure/enqueue", response_model=FailureItemResponse)
async def enqueue_failure(request: FailureEnqueueRequest):
    """Enqueues failed document for retry tracking or DLQ manual review escalation."""
    logger.info(f"Enqueuing failure for document_id={request.document_id}")
    return enqueue_failure_item(request)

@app.post("/failure/retry/{document_id}", response_model=FailureItemResponse)
async def retry_failure(document_id: str):
    """Retries processing of a failed document if retries are not exhausted."""
    try:
        return execute_retry(document_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Document {document_id} not found in failure queue")

@app.get("/failure/dlq", response_model=DLQSummaryResponse)
async def get_dlq_summary():
    """Lists dead-letter queue items requiring manual intervention."""
    items = list_dlq_items()
    manual_count = sum(1 for item in items if item.status == "manual_review")
    return DLQSummaryResponse(
        total_items=len(items),
        manual_review_items=manual_count,
        items=items
    )
