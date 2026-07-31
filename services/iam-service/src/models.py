
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str
    password: str
    mfa_code: str | None = Field(default=None, description="Optional OIDC MFA passcode")

class M2MTokenRequest(BaseModel):
    client_id: str
    client_secret: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_seconds: int = 900
    role: str
    scopes: list[str]
    refresh_token: str | None = None

class VerifyTokenRequest(BaseModel):
    token: str
    required_scope: str | None = None
    required_role: str | None = None

class VerifyTokenResponse(BaseModel):
    valid: bool
    username: str | None = None
    role: str | None = None
    roles: list[str] = Field(default_factory=list)
    scopes: list[str] = Field(default_factory=list)
    has_scope: bool = True
    has_role: bool = True
    error: str | None = None
