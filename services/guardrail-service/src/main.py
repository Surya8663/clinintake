from fastapi import FastAPI, HTTPException

from src.config import settings
from src.logger import logger
from src.models import (
    GroundingVerificationRequest, GroundingVerificationResponse,
    PHIScrubRequest, PHIScrubResponse
)
from src.hallucination_guardrail import verify_clinical_claim_grounding
from src.phi_scrubber import scrub_phi_from_text

app = FastAPI(
    title=settings.service_name,
    description="Cross-Cutting Hallucination Verification Guardrail & PHI Scrubbing Service",
    version="1.0.0"
)

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": settings.service_name
    }

@app.post("/guardrail/verify-grounding", response_model=GroundingVerificationResponse)
async def verify_grounding(request: GroundingVerificationRequest):
    """
    Validates that LLM-generated clinical claims are grounded in literal source evidence spans.
    If a claim is ungrounded or fabricated, BLOCKS the response (blocked=True).
    """
    logger.info("Executing hallucination grounding verification check")
    result = verify_clinical_claim_grounding(request)
    if result.blocked:
        logger.warning(f"Guardrail BLOCKED ungrounded claim: {result.reason}")
    return result

@app.post("/guardrail/scrub-phi", response_model=PHIScrubResponse)
async def scrub_phi(request: PHIScrubRequest):
    """Detects and redacts PHI entities (names, SSNs, DOBs, phone numbers) from text."""
    logger.info("Executing PHI scrubbing redaction check")
    return scrub_phi_from_text(request)
