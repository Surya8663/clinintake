from fastapi import FastAPI, HTTPException

from src.config import settings
from src.logger import logger
from src.models import CQLEvaluateRequest, CQLEvaluateResponse
from src.cql_evaluator import evaluate_cql_rules

app = FastAPI(
    title=settings.service_name,
    description="Deterministic Clinical Quality Language (CQL) Rules Engine",
    version="1.0.0"
)

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": settings.service_name
    }

@app.post("/cql/evaluate", response_model=CQLEvaluateResponse)
async def evaluate_cql(request: CQLEvaluateRequest):
    """Evaluates CQL inclusion and exclusion rules against patient clinical data."""
    logger.info(f"Evaluating CQL rules for patient_id={request.patient_id}")
    if not request.patient_id:
        raise HTTPException(status_code=400, detail="patient_id cannot be empty")

    response = evaluate_cql_rules(
        patient_id=request.patient_id,
        clinical_data=request.clinical_data,
        rule_libraries=request.rule_library or ["Diabetes_Screening", "Hypertension_Control"]
    )
    return response
