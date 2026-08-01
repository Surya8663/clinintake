from fastapi import FastAPI, HTTPException

from src.config import settings
from src.explanation_engine import generate_care_gap_explanation
from src.logger import logger
from src.models import CareGapExplanationResponse, ClinicalDecisionPackage

app = FastAPI(
    title=settings.service_name,
    description="Care-Gap Explanation Agent with Real Guideline & Document Citation Grounding",
    version="1.0.0"
)

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": settings.service_name
    }

@app.post("/care-gap/explain", response_model=CareGapExplanationResponse)
async def explain_care_gaps(package: ClinicalDecisionPackage):
    """Receives ONLY the assembled Clinical Decision Package and generates a grounded explanation citing real passages."""
    logger.info(f"Received Clinical Decision Package for document_id={package.document_id}")

    if not package.document_id:
        raise HTTPException(status_code=400, detail="document_id must be provided in package")

    response = generate_care_gap_explanation(package)
    return response
