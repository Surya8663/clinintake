"""
Persistent Failure Queue Engine (DLQ) backed by PostgreSQL.
Replaces the previously in-memory _DLQ_STORE dict with durable SQL persistence.
Supports exponential backoff retry scheduling, dead-letter escalation,
and authenticated clinician manual re-drive.
"""
import datetime
import math
import random
import logging
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from src.models import FailureQueueRecord, FailureEnqueueRequest, FailureItemResponse
from src.config import settings

logger = logging.getLogger(__name__)


def _next_retry_at(retry_count: int, base_delay_s: float = 30.0) -> datetime.datetime:
    """Calculate next retry timestamp using exponential backoff with jitter."""
    delay = base_delay_s * (2 ** retry_count) + random.uniform(0, 5)
    return datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=delay)


async def enqueue_failure_item(
    db: AsyncSession,
    request: FailureEnqueueRequest,
) -> FailureItemResponse:
    """
    Durably enqueue a failed document for retry.
    If the document already exists, increments retry_count and updates status.
    Upon retry exhaustion, escalates to manual_review dead-letter state.
    """
    now = datetime.datetime.now(datetime.timezone.utc)
    result = await db.execute(
        select(FailureQueueRecord).where(FailureQueueRecord.document_id == request.document_id)
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.retry_count += 1
        existing.error_message = request.error_message
        if existing.retry_count >= settings.max_retries:
            existing.status = "manual_review"
            logger.warning(
                f"DLQ: Retries exhausted for doc_id={request.document_id} "
                f"({existing.retry_count}/{settings.max_retries}). Escalated to manual_review."
            )
        else:
            existing.status = "queued"
            existing.next_retry_at = _next_retry_at(existing.retry_count)
        await db.commit()
        await db.refresh(existing)
        return FailureItemResponse.model_validate(existing)
    else:
        record = FailureQueueRecord(
            document_id=request.document_id,
            service_name=request.service_name,
            error_type=request.error_type,
            error_message=request.error_message,
            retry_count=0,
            max_retries=settings.max_retries,
            status="queued",
            enqueued_at=now,
            next_retry_at=_next_retry_at(0),
        )
        db.add(record)
        await db.commit()
        await db.refresh(record)
        logger.info(f"DLQ: Enqueued doc_id={request.document_id} error_type={request.error_type}")
        return FailureItemResponse.model_validate(record)


async def execute_retry(db: AsyncSession, document_id: str) -> FailureItemResponse:
    """Attempt to retry document; raises if not found or retries exhausted."""
    result = await db.execute(
        select(FailureQueueRecord).where(FailureQueueRecord.document_id == document_id)
    )
    record = result.scalar_one_or_none()
    if not record:
        raise KeyError(f"Document '{document_id}' not found in failure queue.")

    if record.retry_count >= settings.max_retries:
        record.status = "manual_review"
        await db.commit()
        return FailureItemResponse.model_validate(record)

    record.retry_count += 1
    record.status = "retrying" if record.retry_count < settings.max_retries else "manual_review"
    record.next_retry_at = _next_retry_at(record.retry_count)
    await db.commit()
    await db.refresh(record)
    return FailureItemResponse.model_validate(record)


async def manual_redrive(
    db: AsyncSession,
    document_id: str,
    redriven_by: str,
) -> FailureItemResponse:
    """
    Authenticated clinician manually re-drives a dead-letter document.
    Resets retry_count and status, records who initiated the re-drive.
    """
    result = await db.execute(
        select(FailureQueueRecord).where(FailureQueueRecord.document_id == document_id)
    )
    record = result.scalar_one_or_none()
    if not record:
        raise KeyError(f"Document '{document_id}' not found in failure queue for re-drive.")
    if record.status != "manual_review":
        raise ValueError(
            f"Document '{document_id}' is not in manual_review state (current: {record.status})."
        )

    record.retry_count = 0
    record.status = "re_driven_queued"
    record.redriven_by = redriven_by
    record.redriven_at = datetime.datetime.now(datetime.timezone.utc)
    record.next_retry_at = _next_retry_at(0)
    await db.commit()
    await db.refresh(record)
    logger.info(
        f"DLQ: Authenticated re-drive of doc_id={document_id} by clinician={redriven_by}"
    )
    return FailureItemResponse.model_validate(record)


async def list_dlq_items(db: AsyncSession) -> List[FailureItemResponse]:
    """Returns all items in the durable failure queue."""
    result = await db.execute(select(FailureQueueRecord))
    records = result.scalars().all()
    return [FailureItemResponse.model_validate(r) for r in records]
