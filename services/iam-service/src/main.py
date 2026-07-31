from fastapi import FastAPI, HTTPException

from services.common.security_headers import SecurityHeadersMiddleware
from src.config import settings
from src.logger import logger
from src.models import LoginRequest, M2MTokenRequest, TokenResponse, VerifyTokenRequest, VerifyTokenResponse
from src.rbac_engine import (
    authenticate_user_oidc,
    create_m2m_service_token,
    create_short_lived_jwt_access_token,
    verify_jwt_token_scopes,
)

app = FastAPI(
    title=settings.service_name,
    description="Keycloak OIDC Integration Facade and Token Verification Service",
    version="2.0.0"
)

app.add_middleware(SecurityHeadersMiddleware)

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": settings.service_name,
        "oidc_realm": settings.keycloak_realm,
        "token_ttl_minutes": settings.access_token_expire_minutes
    }

@app.post("/iam/auth/login", response_model=TokenResponse)
async def login_oidc(request: LoginRequest):
    """
    Authenticates username and password against Keycloak OIDC provider facade.
    Returns short-lived JWT token (15-min TTL) encoded with role claims.
    """
    logger.info(f"Received OIDC login request for user '{request.username}'")
    success, role, scopes, err_msg = authenticate_user_oidc(request.username, request.password, request.mfa_code)

    if not success:
        raise HTTPException(status_code=401, detail=err_msg or "OIDC authentication failed")

    token, expires_in_sec = create_short_lived_jwt_access_token(request.username, role, scopes)

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in_seconds=expires_in_sec,
        role=role,
        scopes=scopes
    )

@app.post("/iam/auth/token/m2m", response_model=TokenResponse)
async def get_m2m_token(request: M2MTokenRequest):
    """Generates a Machine-to-Machine client credentials token for internal service calls."""
    try:
        token, expires_in_sec = create_m2m_service_token(request.client_id, request.client_secret)
        return TokenResponse(
            access_token=token,
            token_type="bearer",
            expires_in_seconds=expires_in_sec,
            role="CLINICAL_AGENT",
            scopes=["service:internal"]
        )
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

@app.post("/iam/auth/verify", response_model=VerifyTokenResponse)
async def verify_token(request: VerifyTokenRequest):
    """Verifies JWT token signature against Keycloak JWKS and checks required RBAC scope/role."""
    result = verify_jwt_token_scopes(request.token, request.required_scope, request.required_role)
    if not result["valid"]:
        raise HTTPException(status_code=401, detail=result.get("error", "Invalid or expired JWT token"))
    return VerifyTokenResponse(**result)
