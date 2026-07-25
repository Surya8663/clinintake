from fastapi import FastAPI, HTTPException

from src.config import settings
from src.logger import logger
from src.models import InteractionCheckRequest, InteractionCheckResponse
from src.interaction_checker import check_all_interactions

app = FastAPI(
    title=settings.service_name,
    description="Deterministic Drug-Drug and Drug-Allergy Interaction Microservice",
    version="1.0.0"
)

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": settings.service_name
    }

@app.post("/interactions/check", response_model=InteractionCheckResponse)
async def check_interactions(request: InteractionCheckRequest):
    """Checks for drug-drug and drug-allergy interactions against RxNav API and deterministic clinical databases."""
    logger.info(f"Checking interactions for {len(request.medications)} meds and {len(request.allergies)} allergies")
    if not request.medications:
        raise HTTPException(status_code=400, detail="medications list cannot be empty")

    response = await check_all_interactions(request.medications, request.allergies)
    return response
