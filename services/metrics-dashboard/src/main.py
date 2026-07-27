import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from src.config import settings
from src.logger import logger
from src.models import KPISummaryResponse
from src.kpi_engine import calculate_pipeline_kpis

app = FastAPI(
    title=settings.service_name,
    description="Real Pipeline KPI Analytics Dashboard (Extraction Accuracy, Red-Flag Sensitivity, Hallucination Rate)",
    version="1.0.0"
)

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": settings.service_name
    }

@app.get("/metrics/kpis", response_model=KPISummaryResponse)
async def get_pipeline_kpis():
    """
    Computes PRD Section 13 KPIs from actual pipeline evaluation benchmark datasets.
    Returns real accuracy, red-flag sensitivity, and quote-grounding hallucination rate metrics.
    """
    logger.info("Computing pipeline KPI metrics")
    return calculate_pipeline_kpis()

# Mount built frontend UI if dist folder exists
frontend_dist_dir = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.exists(frontend_dist_dir):
    app.mount("/ui", StaticFiles(directory=frontend_dist_dir, html=True), name="frontend")
