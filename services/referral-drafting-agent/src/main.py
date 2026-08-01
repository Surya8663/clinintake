from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from src.config import settings
from src.drafting_engine import ReferralDraftingError, generate_referral_draft_letter
from src.llm_client import LLMInvalidResponseError, LLMUnavailableError
from src.logger import logger
from src.models import ReferralDraftRequest, ReferralDraftResponse

app = FastAPI(title=settings.service_name, description="Referral Drafting Agent for Grounded Specialist Letters", version="1.0.0")


@app.exception_handler(LLMUnavailableError)
async def llm_unavailable_handler(request: Request, exc: LLMUnavailableError):
    logger.error(f"[REFERRAL DRAFTING FAILURE] LLM Service Unavailable: {exc}")
    return JSONResponse(status_code=503, content={"detail": str(exc)})


@app.exception_handler(LLMInvalidResponseError)
async def llm_invalid_response_handler(request: Request, exc: LLMInvalidResponseError):
    logger.error(f"[REFERRAL DRAFTING FAILURE] LLM Invalid Response: {exc}")
    return JSONResponse(status_code=502, content={"detail": str(exc)})


@app.exception_handler(ReferralDraftingError)
async def drafting_error_handler(request: Request, exc: ReferralDraftingError):
    logger.error(f"[REFERRAL DRAFTING FAILURE] Drafting Error: {exc}")
    return JSONResponse(status_code=500, content={"detail": str(exc)})


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": settings.service_name}


@app.post("/referral/draft", response_model=ReferralDraftResponse)
async def draft_referral_letter(request: ExtractRequest if False else ReferralDraftRequest):
    """Generates a real draft referral letter grounded in Clinical Decision Package context."""
    logger.info(f"Received referral drafting request for document_id={request.document_id}")

    if not request.document_id:
        raise HTTPException(status_code=400, detail="document_id must be provided")

    response = generate_referral_draft_letter(request)
    return response
