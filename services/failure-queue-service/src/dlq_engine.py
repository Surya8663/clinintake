import datetime
from typing import Dict, Any, List, Optional
from src.config import settings
from src.models import FailureEnqueueRequest, FailureItemResponse
from src.logger import logger

# In-memory store for DLQ items
_DLQ_STORE: Dict[str, Dict[str, Any]] = {}

def enqueue_failure_item(request: FailureEnqueueRequest) -> FailureItemResponse:
    """Enqueues a failed document and tracks retry count."""
    doc_id = request.document_id
    now_iso = datetime.datetime.utcnow().isoformat() + "Z"

    if doc_id in _DLQ_STORE:
        item = _DLQ_STORE[doc_id]
        item["retry_count"] += 1
        item["error_message"] = request.error_message
        if item["retry_count"] >= settings.max_retries:
            item["status"] = "manual_review"
            logger.warning(f"Exhausted retries ({item['retry_count']}/{settings.max_retries}) for doc_id={doc_id}. Escalated to manual_review state.")
        else:
            item["status"] = "queued"
    else:
        item = {
            "document_id": doc_id,
            "service_name": request.service_name,
            "error_type": request.error_type,
            "error_message": request.error_message,
            "retry_count": 0,
            "max_retries": settings.max_retries,
            "status": "queued",
            "enqueued_at": now_iso
        }
        _DLQ_STORE[doc_id] = item
        logger.info(f"Enqueued failed item doc_id={doc_id} error_type={request.error_type}")

    return FailureItemResponse(**item)

def execute_retry(document_id: str) -> FailureItemResponse:
    """Attempts to retry document processing if retry count is below threshold."""
    if document_id not in _DLQ_STORE:
        raise KeyError(f"Document {document_id} not found in failure queue")

    item = _DLQ_STORE[document_id]
    if item["retry_count"] >= settings.max_retries:
        item["status"] = "manual_review"
        logger.warning(f"Cannot retry doc_id={document_id}: Retries exhausted ({item['retry_count']}/{settings.max_retries}). Item in manual_review.")
        return FailureItemResponse(**item)

    item["retry_count"] += 1
    if item["retry_count"] >= settings.max_retries:
        item["status"] = "manual_review"
    else:
        item["status"] = "retrying"

    return FailureItemResponse(**item)

def list_dlq_items() -> List[FailureItemResponse]:
    """Returns list of all dead-letter queue items."""
    return [FailureItemResponse(**item) for item in _DLQ_STORE.values()]
