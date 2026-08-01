from fastapi import FastAPI

from src.config import settings
from src.logger import logger
from src.models import TemporalEvaluateRequest, TemporalEvaluateResponse
from src.temporal_calculator import calculate_temporal_care_gap

app = FastAPI(title=settings.service_name, description="Deterministic Temporal Date Arithmetic Care Gap Reasoning Engine", version="1.0.0")


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": settings.service_name}


@app.post("/temporal/evaluate", response_model=TemporalEvaluateResponse)
async def evaluate_temporal_care_gap(request: TemporalEvaluateRequest):
    """Computes exact screening status ('due', 'overdue', 'not-due', 'insufficient-information')."""
    logger.info(f"Evaluating temporal gap for procedure='{request.procedure_name}'")
    response = calculate_temporal_care_gap(request)
    return response
