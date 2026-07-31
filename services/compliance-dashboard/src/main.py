import os
from typing import Any

from fastapi import Depends, FastAPI
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles

from services.common.jwt_verifier import require_roles, security_bearer
from services.common.security_headers import SecurityHeadersMiddleware
from src.audit_client import fetch_audit_events_via_api, fetch_vault_integrity_via_api
from src.config import settings

app = FastAPI(
    title=settings.service_name,
    description="Compliance Dashboard REST API & UI querying audit-service API exclusively",
    version="2.0.0"
)

app.add_middleware(SecurityHeadersMiddleware)

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": settings.service_name,
        "audit_service_url": settings.audit_service_url
    }

@app.get("/compliance/audit-trail")
async def get_compliance_audit_trail(
    document_id: str | None = None,
    service_name: str | None = None,
    event_type: str | None = None,
    credentials: HTTPAuthorizationCredentials | None = Depends(security_bearer),
    claims: dict[str, Any] = Depends(require_roles(["compliance:audit:read", "admin:system"]))
):
    """
    Exposes audit log trail to compliance reviewers.
    Enforces 'compliance:audit:read' role and forwards verified token.
    """
    token_str = credentials.credentials if credentials else None
    return await fetch_audit_events_via_api(document_id, service_name, event_type, auth_token=token_str)

@app.get("/compliance/verify-vault")
async def verify_compliance_vault(
    credentials: HTTPAuthorizationCredentials | None = Depends(security_bearer),
    claims: dict[str, Any] = Depends(require_roles(["compliance:audit:read", "admin:system"]))
):
    """Exposes cryptographic hash chain & HMAC signature verification status."""
    token_str = credentials.credentials if credentials else None
    return await fetch_vault_integrity_via_api(auth_token=token_str)

# Mount built frontend UI if dist folder exists
frontend_dist_dir = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.exists(frontend_dist_dir):
    app.mount("/ui", StaticFiles(directory=frontend_dist_dir, html=True), name="frontend")
