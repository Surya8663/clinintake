from fastapi import FastAPI, HTTPException

from src.config import settings
from src.logger import logger
from src.models import LoginRequest, TokenResponse, VerifyTokenRequest, VerifyTokenResponse
from src.rbac_engine import authenticate_user_mfa, create_short_lived_jwt_access_token, verify_jwt_token_scopes

app = FastAPI(
    title=settings.service_name,
    description="MFA Authentication and Fine-Grained RBAC Scope Authorization Service",
    version="1.0.0"
)

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": settings.service_name,
        "token_ttl_minutes": settings.access_token_expire_minutes
    }

@app.post("/iam/auth/login", response_model=TokenResponse)
async def login_with_mfa(request: LoginRequest):
    """
    Authenticates username, password, and mandatory MFA code.
    Returns short-lived JWT token (15-min TTL) encoded with role-based scopes.
    """
    logger.info(f"Received MFA login request for user '{request.username}'")
    success, role, scopes, err_msg = authenticate_user_mfa(request.username, request.password, request.mfa_code)

    if not success:
        raise HTTPException(status_code=401, detail=err_msg or "MFA authentication failed")

    token, expires_in_sec = create_short_lived_jwt_access_token(request.username, role, scopes)

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in_seconds=expires_in_sec,
        role=role,
        scopes=scopes
    )

@app.post("/iam/auth/verify", response_model=VerifyTokenResponse)
async def verify_token(request: VerifyTokenRequest):
    """Verifies JWT token validity and checks presence of required RBAC scope."""
    result = verify_jwt_token_scopes(request.token, request.required_scope)
    if not result["valid"]:
        raise HTTPException(status_code=401, detail=result.get("error", "Invalid or expired JWT token"))
    return VerifyTokenResponse(**result)
