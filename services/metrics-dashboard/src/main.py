import os
from typing import Any

from fastapi import Depends, FastAPI
from fastapi.staticfiles import StaticFiles

from services.common.jwt_verifier import require_roles
from services.common.security_headers import SecurityHeadersMiddleware
from src.config import settings
from src.kpi_engine import calculate_pipeline_kpis
from src.logger import logger
from src.models import KPISummaryResponse

app = FastAPI(title=settings.service_name, description="Real Pipeline KPI Analytics Dashboard (Extraction Accuracy, Red-Flag Sensitivity, Hallucination Rate)", version="2.0.0")

app.add_middleware(SecurityHeadersMiddleware)


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": settings.service_name}


@app.get("/metrics/kpis", response_model=KPISummaryResponse)
async def get_pipeline_kpis(claims: dict[str, Any] = Depends(require_roles(["quality:metrics:read", "admin:system"]))):
    """
    Computes PRD Section 13 KPIs from actual pipeline evaluation benchmark datasets.
    Enforces 'quality:metrics:read' RBAC role requirement.
    """
    logger.info("Computing pipeline KPI metrics for verified user")
    return calculate_pipeline_kpis()


# Mount built frontend UI if dist folder exists
frontend_dist_dir = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.exists(frontend_dist_dir):
    app.mount("/ui", StaticFiles(directory=frontend_dist_dir, html=True), name="frontend")
