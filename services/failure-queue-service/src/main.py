from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.database import engine, get_db
from src.dlq_engine import enqueue_failure_item, execute_retry, list_dlq_items
from src.logger import logger
from src.models import Base, DLQSummaryResponse, FailureEnqueueRequest, FailureItemResponse

app = FastAPI(
    title=settings.service_name,
    description="Dead-Letter Queue with Retry Tracking and Manual Escalation",
    version="1.0.0"
)


@app.on_event("startup")
async def startup_event():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": settings.service_name,
        "max_retries": settings.max_retries
    }


@app.post("/failure/enqueue", response_model=FailureItemResponse)
async def enqueue_failure(request: FailureEnqueueRequest, db: AsyncSession = Depends(get_db)):
    """Enqueues failed document for retry tracking or DLQ manual review escalation."""
    logger.info(f"Enqueuing failure for document_id={request.document_id}")
    return await enqueue_failure_item(db, request)


@app.post("/failure/retry/{document_id}", response_model=FailureItemResponse)
async def retry_failure(document_id: str, db: AsyncSession = Depends(get_db)):
    """Retries processing of a failed document if retries are not exhausted."""
    try:
        return await execute_retry(db, document_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Document {document_id} not found in failure queue")


@app.get("/failure/dlq", response_model=DLQSummaryResponse)
async def get_dlq_summary(db: AsyncSession = Depends(get_db)):
    """Lists dead-letter queue items requiring manual intervention."""
    items = await list_dlq_items(db)
    manual_count = sum(1 for item in items if item.status == "manual_review")
    return DLQSummaryResponse(
        total_items=len(items),
        manual_review_items=manual_count,
        items=items
    )
