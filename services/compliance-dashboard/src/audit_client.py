from typing import Any

import httpx

from src.config import settings
from src.logger import logger


async def fetch_audit_events_via_api(document_id: str | None = None, service_name: str | None = None, event_type: str | None = None, auth_token: str | None = None) -> dict[str, Any]:
    """
    Fetches audit trail logs EXCLUSIVELY via audit-service REST API endpoint GET /audit/events.
    Forwards verified Bearer auth token for authorization.
    """
    params = {}
    if document_id:
        params["document_id"] = document_id
    if service_name:
        params["service_name"] = service_name
    if event_type:
        params["event_type"] = event_type

    headers = {}
    if auth_token:
        headers["Authorization"] = auth_token if auth_token.startswith("Bearer ") else f"Bearer {auth_token}"

    url = f"{settings.audit_service_url}/audit/events"
    logger.info(f"Compliance Dashboard querying audit-service REST API at {url}")

    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(url, params=params, headers=headers)
            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code == 403:
                logger.warning(f"Audit API returned 403 Forbidden: {resp.text}")
                return {"total_records": 0, "records": [], "error": "Missing required 'compliance:audit:read' RBAC role"}
            elif resp.status_code == 401:
                return {"total_records": 0, "records": [], "error": "Unauthorized: invalid or missing token"}
            else:
                logger.warning(f"Audit API returned status {resp.status_code}")
                return {"total_records": 0, "records": []}
    except Exception as e:
        logger.warning(f"Failed to query audit-service REST API ({e}). Service unreachable.")
        return {"total_records": 0, "records": [], "error": "audit-service unreachable", "status": "error"}


async def fetch_vault_integrity_via_api(auth_token: str | None = None) -> dict[str, Any]:
    """Fetches cryptographic vault integrity verification via audit-service REST API GET /audit/verify."""
    url = f"{settings.audit_service_url}/audit/verify"
    headers = {}
    if auth_token:
        headers["Authorization"] = auth_token if auth_token.startswith("Bearer ") else f"Bearer {auth_token}"

    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code == 200:
                return resp.json()
    except Exception as e:
        logger.warning(f"Failed to query vault integrity API ({e})")

    return {"status": "unreachable", "error": "vault integrity check unavailable"}
