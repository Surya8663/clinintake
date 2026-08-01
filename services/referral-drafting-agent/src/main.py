from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from src.config import settings
from src.drafting_engine import ReferralDraftingError, ReferralValidationError, generate_referral_draft_letter
from src.llm_client import (
    LLMInvalidResponseError,
    LLMRequestError,
    LLMRateLimitError,
    LLMServiceError,
    LLMTimeoutError,
    LLMUnavailableError,
)
from src.logger import logger
from src.models import ReferralDraftRequest, ReferralDraftResponse

app = FastAPI(title=settings.service_name, description="Referral Drafting Agent for Grounded Specialist Letters", version="1.0.0")


@app.exception_handler(ReferralValidationError)
async def referral_validation_handler(request: Request, exc: ReferralValidationError):
    logger.warning(f"[REFERRAL VALIDATION FAILURE] {exc}")
    return JSONResponse(status_code=422, content={"detail": str(exc)})


@app.exception_handler(LLMUnavailableError)
@app.exception_handler(LLMTimeoutError)
@app.exception_handler(LLMRateLimitError)
async def llm_unavailable_handler(request: Request, exc: Exception):
    logger.error(f"[REFERRAL DRAFTING FAILURE] LLM Service Unavailable/Timeout: {exc}")
    return JSONResponse(status_code=503, content={"detail": str(exc)})


@app.exception_handler(LLMServiceError)
@app.exception_handler(LLMInvalidResponseError)
@app.exception_handler(ReferralDraftingError)
async def llm_invalid_response_handler(request: Request, exc: Exception):
    logger.error(f"[REFERRAL DRAFTING FAILURE] LLM Invalid Response/Service Error: {exc}")
    return JSONResponse(status_code=502, content={"detail": str(exc)})


@app.exception_handler(LLMRequestError)
async def llm_request_handler(request: Request, exc: LLMRequestError):
    logger.warning(f"[REFERRAL DRAFTING REQUEST ERROR] {exc}")
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": settings.service_name}


@app.post("/referral/draft", response_model=ReferralDraftResponse)
async def draft_referral_letter(request: ReferralDraftRequest):
    """Generates a real draft referral letter grounded in Clinical Decision Package context."""
    logger.info(f"Received referral drafting request for document_id={request.document_id}")

    if not request.document_id:
        raise HTTPException(status_code=400, detail="document_id must be provided")

    response = generate_referral_draft_letter(request)
    return response
