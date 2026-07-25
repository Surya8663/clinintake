import time
from fastapi import FastAPI, HTTPException

from src.config import settings
from src.logger import logger
from src.models import SafetyEvaluateRequest, SafetyEvaluateResponse
from src.news2_engine import calculate_news2_points
from src.redflag_detector import detect_clinical_redflags

app = FastAPI(
    title=settings.service_name,
    description="Emergency Safety Sub-Agent & Interrupt Lane",
    version="1.0.0"
)

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": settings.service_name
    }

@app.post("/safety/evaluate", response_model=SafetyEvaluateResponse)
async def evaluate_clinical_safety(request: SafetyEvaluateRequest):
    """Evaluates emergency clinical safety, NEWS2 points, qSOFA criteria, and red flags."""
    start_time = time.time()
    logger.info(f"Evaluating clinical safety for document_id={request.document_id}")

    news2_score, qsofa_score, status, rationale = calculate_news2_points(request.vitals)

    red_flags = detect_clinical_redflags(
        clinical_text=request.clinical_text,
        symptoms=request.symptoms,
        vitals=request.vitals,
        news2_score=news2_score,
        qsofa_score=qsofa_score
    )

    is_emergency = len(red_flags) > 0 or (news2_score is not None and news2_score >= 7)

    latency_ms = round((time.time() - start_time) * 1000.0, 2)
    logger.info(f"Safety evaluation complete in {latency_ms}ms: is_emergency={is_emergency}, red_flags={len(red_flags)}, status={status}")

    return SafetyEvaluateResponse(
        document_id=request.document_id,
        is_emergency=is_emergency,
        news2_score=news2_score,
        qsofa_score=qsofa_score,
        red_flags=red_flags,
        assessment_status=status,
        rationale=rationale,
        latency_ms=latency_ms
    )
