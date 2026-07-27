import os
from typing import Optional
from fastapi import FastAPI, Header
from fastapi.staticfiles import StaticFiles

from src.config import settings
from src.logger import logger
from src.audit_client import fetch_audit_events_via_api, fetch_vault_integrity_via_api

app = FastAPI(
    title=settings.service_name,
    description="Compliance Dashboard REST API & UI querying audit-service API exclusively",
    version="1.0.0"
)

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": settings.service_name,
        "audit_service_url": settings.audit_service_url
    }

@app.get("/compliance/audit-trail")
async def get_compliance_audit_trail(
    document_id: Optional[str] = None,
    service_name: Optional[str] = None,
    event_type: Optional[str] = None,
    x_user_scopes: Optional[str] = Header("audit:read", alias="X-User-Scopes")
):
    """
    Exposes audit log trail to compliance reviewers.
    Data is fetched EXCLUSIVELY via audit-service HTTP REST API. Zero direct DB access.
    """
    return await fetch_audit_events_via_api(document_id, service_name, event_type, x_user_scopes)

@app.get("/compliance/verify-vault")
async def verify_compliance_vault():
    """Exposes cryptographic hash chain & HMAC signature verification status."""
    return await fetch_vault_integrity_via_api()

# Mount built frontend UI if dist folder exists
frontend_dist_dir = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.exists(frontend_dist_dir):
    app.mount("/ui", StaticFiles(directory=frontend_dist_dir, html=True), name="frontend")
