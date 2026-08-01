import time

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
import httpx

from src.config import settings
from src.extractor import perform_quote_grounded_extraction
from src.fhir_validator import build_and_validate_fhir_resources
from src.llm_client import (
    LLMGovernanceViolationError,
    LLMInvalidResponseError,
    LLMRequestError,
    LLMRateLimitError,
    LLMServiceError,
    LLMTimeoutError,
    LLMUnavailableError,
)
from src.logger import logger
from src.models import ExtractRequest, ExtractResponse


class SafetyServiceTimeoutError(Exception):
    """Raised when Safety Sub-Agent evaluation times out."""


class SafetyServiceUnavailableError(Exception):
    """Raised when Safety Sub-Agent service is network-unavailable or connection fails."""


class SafetyRequestError(Exception):
    """Raised when Safety Sub-Agent returns a 4xx client request error."""


class SafetyServiceError(Exception):
    """Raised when Safety Sub-Agent returns a 5xx server error."""


class SafetyInvalidResponseError(Exception):
    """Raised when Safety Sub-Agent returns a malformed or invalid response payload."""


app = FastAPI(title=settings.service_name, description="Quote-Grounded LLM Extraction Agent with FHIR R4 Validation and Direct Emergency Safety Interrupt", version="1.0.0")


@app.exception_handler(LLMUnavailableError)
@app.exception_handler(LLMTimeoutError)
@app.exception_handler(LLMRateLimitError)
async def llm_unavailable_handler(request: Request, exc: Exception):
    logger.error(f"[EXTRACTION FAILURE] LLM Service Unavailable/Timeout: {exc}")
    return JSONResponse(status_code=503, content={"detail": f"Extraction LLM Service Unavailable: {exc!s}"})


@app.exception_handler(LLMServiceError)
@app.exception_handler(LLMInvalidResponseError)
async def llm_invalid_response_handler(request: Request, exc: Exception):
    logger.error(f"[EXTRACTION FAILURE] LLM Service/Response Error: {exc}")
    return JSONResponse(status_code=502, content={"detail": f"Extraction LLM Invalid Response: {exc!s}"})


@app.exception_handler(LLMRequestError)
@app.exception_handler(LLMGovernanceViolationError)
async def llm_governance_handler(request: Request, exc: Exception):
    logger.warning(f"[EXTRACTION GOVERNANCE/REQUEST ERROR] {exc}")
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.exception_handler(SafetyServiceTimeoutError)
@app.exception_handler(SafetyServiceUnavailableError)
async def safety_unavailable_handler(request: Request, exc: Exception):
    logger.error(f"[SAFETY FAILURE] Safety Sub-Agent Service Unavailable/Timeout: {exc}")
    return JSONResponse(status_code=503, content={"detail": f"Safety Sub-Agent Unavailable: {exc!s}"})


@app.exception_handler(SafetyServiceError)
@app.exception_handler(SafetyInvalidResponseError)
async def safety_service_handler(request: Request, exc: Exception):
    logger.error(f"[SAFETY FAILURE] Safety Sub-Agent Service/Response Error: {exc}")
    return JSONResponse(status_code=502, content={"detail": f"Safety Sub-Agent Error: {exc!s}"})


@app.exception_handler(SafetyRequestError)
async def safety_request_handler(request: Request, exc: SafetyRequestError):
    logger.error(f"[SAFETY FAILURE] Safety Sub-Agent Request Error: {exc}")
    return JSONResponse(status_code=400, content={"detail": f"Safety Sub-Agent Request Error: {exc!s}"})


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": settings.service_name, "confidence_threshold": settings.confidence_threshold}


@app.post("/extract", response_model=ExtractResponse)
async def extract_clinical_data(request: ExtractRequest):
    """Performs Quote-Grounded extraction, FHIR R4 validation, and direct Emergency Safety Interrupt evaluation."""
    logger.info(f"Extracting clinical data for document_id={request.document_id}")

    ocr_text = request.ocr_text or ""
    ocr_words = request.ocr_words or []

    if not ocr_text:
        raise HTTPException(status_code=400, detail="ocr_text must be provided")

    extracted_data = perform_quote_grounded_extraction(ocr_text=ocr_text, ocr_words=ocr_words, threshold_override=settings.confidence_threshold)

    fhir_resources = build_and_validate_fhir_resources(extracted_data)

    # Compute overall confidence
    scores = [extracted_data.patient_id.confidence]
    for d in extracted_data.diagnoses:
        scores.append(d.name.confidence)
    for m in extracted_data.medications:
        scores.append(m.name.confidence)
    for l in extracted_data.labs:
        scores.append(l.name.confidence)

    overall_confidence = round(sum(scores) / max(len(scores), 1), 2)

    # Direct Emergency Safety Interrupt Evaluation (Fail Closed — No local keyword fallbacks)
    safety_triggered = False
    safety_res = None
    latency_ms = 0.0

    start_safety = time.time()
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            safety_payload = {
                "document_id": request.document_id,
                "patient_id": extracted_data.patient_id.value,
                "clinical_text": ocr_text,
                "symptoms": [d.name.value for d in extracted_data.diagnoses],
            }
            resp = await client.post(f"{settings.safety_sub_agent_url}/safety/evaluate", json=safety_payload)
            latency_ms = round((time.time() - start_safety) * 1000.0, 2)
            if resp.status_code == 200:
                try:
                    safety_res = resp.json()
                except Exception as json_err:
                    raise SafetyInvalidResponseError("Safety Sub-Agent returned malformed JSON payload") from json_err

                if not isinstance(safety_res, dict):
                    raise SafetyInvalidResponseError("Safety Sub-Agent response is not a JSON object")

                safety_triggered = bool(safety_res.get("is_emergency", False))
                logger.info(f"Direct Emergency Safety Interrupt evaluation finished in {latency_ms}ms: is_emergency={safety_triggered}")
            elif 400 <= resp.status_code < 500:
                raise SafetyRequestError(f"Safety Sub-Agent returned HTTP client error {resp.status_code}: {resp.text}")
            else:
                raise SafetyServiceError(f"Safety Sub-Agent returned HTTP server error {resp.status_code}: {resp.text}")

    except httpx.TimeoutException as e:
        logger.error(f"Safety Sub-Agent request timed out: {e}")
        raise SafetyServiceTimeoutError(f"Safety Sub-Agent timed out: {e}") from e
    except (httpx.ConnectError, httpx.NetworkError, httpx.RequestError, httpx.HTTPError) as e:
        logger.error(f"Safety Sub-Agent connection error: {e}")
        raise SafetyServiceUnavailableError(f"Safety Sub-Agent service unavailable: {e}") from e
    except Exception as e:
        if isinstance(e, (SafetyServiceTimeoutError, SafetyServiceUnavailableError, SafetyRequestError, SafetyServiceError, SafetyInvalidResponseError)):
            raise
        logger.error(f"Safety Sub-Agent error: {e}")
        raise SafetyServiceUnavailableError(f"Safety Sub-Agent service unavailable: {e}") from e

    return ExtractResponse(
        document_id=request.document_id,
        extracted_data=extracted_data,
        fhir_resources=fhir_resources,
        overall_confidence=overall_confidence,
        safety_interrupt_triggered=safety_triggered,
        safety_response=safety_res,
        safety_interrupt_latency_ms=latency_ms,
    )
