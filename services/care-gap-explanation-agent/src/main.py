from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from src.config import settings
from src.explanation_engine import GroundingVerificationError, generate_care_gap_explanation
from src.llm_client import LLMInvalidResponseError, LLMUnavailableError
from src.logger import logger
from src.models import CareGapExplanationResponse, ClinicalDecisionPackage

app = FastAPI(title=settings.service_name, description="Care-Gap Explanation Agent with Real Guideline & Document Citation Grounding", version="1.0.0")


@app.exception_handler(GroundingVerificationError)
async def grounding_error_handler(request: Request, exc: GroundingVerificationError):
    logger.error(f"[EXPLANATION FAILURE] Grounding Verification Error: {exc}")
    return JSONResponse(status_code=422, content={"detail": str(exc)})


@app.exception_handler(LLMUnavailableError)
async def llm_unavailable_handler(request: Request, exc: LLMUnavailableError):
    logger.error(f"[EXPLANATION FAILURE] LLM Unavailable Error: {exc}")
    return JSONResponse(status_code=503, content={"detail": str(exc)})


@app.exception_handler(LLMInvalidResponseError)
async def llm_invalid_response_handler(request: Request, exc: LLMInvalidResponseError):
    logger.error(f"[EXPLANATION FAILURE] LLM Invalid Response Error: {exc}")
    return JSONResponse(status_code=502, content={"detail": str(exc)})


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": settings.service_name}


@app.post("/care-gap/explain", response_model=CareGapExplanationResponse)
async def explain_care_gaps(package: ClinicalDecisionPackage):
    """Receives ONLY the assembled Clinical Decision Package and generates a grounded explanation citing real passages."""
    logger.info(f"Received Clinical Decision Package for document_id={package.document_id}")

    if not package.document_id:
        raise HTTPException(status_code=400, detail="document_id must be provided in package")

    response = generate_care_gap_explanation(package)
    return response
