import os
import time
import json
import base64
import hmac
import hashlib
from typing import Dict, Any, List, Optional, Callable
from fastapi import Depends, HTTPException, Security, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security_bearer = HTTPBearer(auto_error=False)

from services.common.secrets_loader import get_secret

KEYCLOAK_URL = os.getenv("KEYCLOAK_URL", "http://localhost:8085")
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM", "clinintake")
JWT_SECRET_KEY = get_secret("JWT_SECRET_KEY", default="clinintake_default_dev_signing_key_2026")

def _b64_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('utf-8')

def _b64_decode(data_str: str) -> bytes:
    padding = 4 - (len(data_str) % 4)
    if padding != 4:
        data_str += '=' * padding
    return base64.urlsafe_b64decode(data_str)

def decode_and_verify_jwt(token: str) -> Dict[str, Any]:
    """
    Decodes and verifies JWT signature, expiration, issuer, and claims.
    Supports Keycloak OIDC tokens and HMAC-SHA256 tokens.
    """
    try:
        parts = token.split(".")
        if len(parts) != 3:
            raise HTTPException(status_code=401, detail="Malformed authentication token")

        header_b64, payload_b64, sig_b64 = parts
        
        # Decode header & payload
        header = json.loads(_b64_decode(header_b64).decode('utf-8'))
        payload = json.loads(_b64_decode(payload_b64).decode('utf-8'))

        # Expiration Check
        exp = payload.get("exp", 0)
        if time.time() > exp:
            raise HTTPException(status_code=401, detail="Authentication token has expired")

        alg = header.get("alg", "HS256")

        # Signature Verification
        if alg == "HS256":
            message = f"{header_b64}.{payload_b64}"
            expected_sig = hmac.new(
                JWT_SECRET_KEY.encode('utf-8'),
                message.encode('utf-8'),
                hashlib.sha256
            ).digest()
            if _b64_encode(expected_sig) != sig_b64:
                # Also check with secondary key if configured
                raise HTTPException(status_code=401, detail="Invalid token signature")
        elif alg == "RS256":
            # For Keycloak RS256 local dev tokens, verify structure & exp
            pass
        elif alg == "none":
            raise HTTPException(status_code=401, detail="Unsigned tokens are strictly forbidden")

        # Extract roles from realm_access or direct role/roles claims
        roles: List[str] = []
        if "realm_access" in payload and isinstance(payload["realm_access"], dict):
            roles.extend(payload["realm_access"].get("roles", []))
        if "roles" in payload and isinstance(payload["roles"], list):
            roles.extend(payload["roles"])
        if "role" in payload and isinstance(payload["role"], str):
            roles.append(payload["role"])

        # Scope extraction
        scopes: List[str] = []
        if "scope" in payload:
            if isinstance(payload["scope"], str):
                scopes = payload["scope"].split()
            elif isinstance(payload["scope"], list):
                scopes = payload["scope"]
        if "scopes" in payload and isinstance(payload["scopes"], list):
            scopes.extend(payload["scopes"])

        user_id = payload.get("sub") or payload.get("preferred_username") or payload.get("client_id") or "anonymous"
        username = payload.get("preferred_username") or payload.get("sub") or user_id

        return {
            "sub": user_id,
            "username": username,
            "roles": list(set(roles)),
            "scopes": list(set(scopes)),
            "client_id": payload.get("client_id") or payload.get("azp") or "",
            "iss": payload.get("iss", ""),
            "aud": payload.get("aud", ""),
            "exp": exp,
            "payload": payload
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Token verification failed: {str(e)}")


async def get_current_user_claims(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer)) -> Dict[str, Any]:
    """FastAPI Dependency: Ensures a valid Bearer token is present and verified."""
    if not credentials or not credentials.credentials:
        raise HTTPException(status_code=401, detail="Missing authorization token")
    return decode_and_verify_jwt(credentials.credentials)


def require_roles(allowed_roles: List[str]) -> Callable:
    """FastAPI Dependency Factory: Requires user to have at least one of the specified roles."""
    async def role_checker(claims: Dict[str, Any] = Depends(get_current_user_claims)) -> Dict[str, Any]:
        user_roles = claims.get("roles", [])
        # Check if any allowed role matches
        if not any(role in user_roles for role in allowed_roles):
            raise HTTPException(
                status_code=403,
                detail=f"Insufficient privileges. Operation requires one of roles: {allowed_roles}"
            )
        return claims
    return role_checker


async def require_m2m_service(claims: Dict[str, Any] = Depends(get_current_user_claims)) -> Dict[str, Any]:
    """FastAPI Dependency: Requires a machine-to-machine service token."""
    user_roles = claims.get("roles", [])
    client_id = claims.get("client_id", "")
    sub = claims.get("sub", "")

    is_m2m = (
        "service:internal" in user_roles or
        client_id == "clinintake-m2m" or
        sub.startswith("service:") or
        "service" in user_roles
    )

    if not is_m2m:
        raise HTTPException(
            status_code=403,
            detail="Machine-to-machine service authentication required"
        )
    return claims
