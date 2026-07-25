from fastapi import FastAPI, HTTPException

from src.config import settings
from src.logger import logger
from src.models import TerminologyMapRequest, TerminologyMapResponse
from src.resolver import resolve_terminology

app = FastAPI(
    title=settings.service_name,
    description="Clinical Terminology Normalization Service (RxNorm, LOINC, SNOMED CT)",
    version="1.0.0"
)

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": settings.service_name,
        "confidence_threshold": settings.confidence_threshold
    }

@app.post("/terminology/map", response_model=TerminologyMapResponse)
async def map_clinical_term(request: TerminologyMapRequest):
    """Maps clinical terms to RxNorm, LOINC, or SNOMED CT with confidence scoring and escalation handling."""
    logger.info(f"Mapping term='{request.term}' for system={request.code_system}")
    if not request.term.strip():
        raise HTTPException(status_code=400, detail="term cannot be empty")

    response = await resolve_terminology(request.term, request.code_system)
    return response
