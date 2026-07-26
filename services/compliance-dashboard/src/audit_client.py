import httpx
from typing import Dict, Any, Optional
from src.config import settings
from src.logger import logger

async def fetch_audit_events_via_api(
    document_id: Optional[str] = None,
    service_name: Optional[str] = None,
    event_type: Optional[str] = None,
    user_scopes: str = "audit:read"
) -> Dict[str, Any]:
    """
    Fetches audit trail logs EXCLUSIVELY via audit-service REST API endpoint GET /audit/events.
    Enforces architectural separation: ZERO direct database connections.
    """
    params = {}
    if document_id:
        params["document_id"] = document_id
    if service_name:
        params["service_name"] = service_name
    if event_type:
        params["event_type"] = event_type

    headers = {
        "X-User-Scopes": user_scopes
    }

    url = f"{settings.audit_service_url}/audit/events"
    logger.info(f"Compliance Dashboard querying audit-service REST API at {url}")

    try:
        async with httpx.AsyncClient(timeout=0.3) as client:
            resp = await client.get(url, params=params, headers=headers)
            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code == 403:
                logger.warning(f"Audit API returned 403 Forbidden: {resp.text}")
                return {"total_records": 0, "records": [], "error": "Missing required 'audit:read' RBAC scope"}
            else:
                logger.warning(f"Audit API returned status {resp.status_code}")
                return {"total_records": 0, "records": []}
    except Exception as e:
        logger.warning(f"Failed to query audit-service REST API ({e}). Service unreachable.")
        return {
            "total_records": 0,
            "records": [],
            "error": "audit-service unreachable",
            "status": "error"
        }

async def fetch_vault_integrity_via_api() -> Dict[str, Any]:
    """Fetches cryptographic vault integrity verification via audit-service REST API GET /audit/verify."""
    url = f"{settings.audit_service_url}/audit/verify"
    try:
        async with httpx.AsyncClient(timeout=0.3) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                return resp.json()
    except Exception as e:
        logger.warning(f"Failed to query vault integrity API ({e})")

    return {
        "status": "unreachable",
        "error": "vault integrity check unavailable"
    }
