import datetime
from fastapi import FastAPI, HTTPException

from src.config import settings
from src.logger import logger
from src.models import FHIRTransactionRequest, FHIRTransactionResponse
from src.idempotency_store import check_and_set_idempotency_key
from src.fhir_bundle_writer import assemble_fhir_r4_transaction_bundle, execute_fhir_transaction

app = FastAPI(
    title=settings.service_name,
    description="Sole EHR Write Component with Redis Idempotency and FHIR R4 Transaction Bundles",
    version="1.0.0"
)

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": settings.service_name,
        "ehr_client_configured": bool(settings.ehr_client_id)
    }

@app.post("/fhir/write-transaction", response_model=FHIRTransactionResponse)
async def write_fhir_transaction(request: FHIRTransactionRequest):
    """
    Sole component with EHR write credentials.
    Enforces Redis-backed idempotency deduplication before executing real FHIR R4 transaction writes.
    """
    logger.info(f"Received FHIR write transaction request doc_id={request.document_id} key={request.idempotency_key}")

    if not request.idempotency_key:
        raise HTTPException(status_code=400, detail="idempotency_key must be provided for EHR write transactions")

    # 1. Check Redis Idempotency Key (Suppress duplicate writes as no-op)
    is_dup, cached_res = check_and_set_idempotency_key(request.idempotency_key)
    if is_dup and cached_res:
        logger.info(f"Duplicate transaction key detected: '{request.idempotency_key}'. Returning cached no-op response.")
        cached_res["is_duplicate"] = True
        cached_res["status"] = "no_op_duplicate_suppressed"
        return FHIRTransactionResponse(**cached_res)

    # 2. Assemble real FHIR R4 Transaction Bundle
    bundle = assemble_fhir_r4_transaction_bundle(
        document_id=request.document_id,
        patient_id=request.patient_id,
        fhir_resources=request.fhir_resources
    )

    # 3. Execute write against local HAPI FHIR server & verify persistence
    bundle_id, references = await execute_fhir_transaction(bundle)

    now_iso = datetime.datetime.utcnow().isoformat() + "Z"
    response_payload = {
        "document_id": request.document_id,
        "status": "persisted",
        "fhir_bundle_id": bundle_id,
        "resource_references": references,
        "is_duplicate": False,
        "timestamp": now_iso
    }

    # 4. Save to Idempotency Store
    check_and_set_idempotency_key(request.idempotency_key, response_payload)

    return FHIRTransactionResponse(**response_payload)
