from pydantic import BaseModel, Field
from typing import List, Optional

class LoginRequest(BaseModel):
    username: str
    password: str
    mfa_code: Optional[str] = Field(default=None, description="Optional OIDC MFA passcode")

class M2MTokenRequest(BaseModel):
    client_id: str
    client_secret: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_seconds: int = 900
    role: str
    scopes: List[str]
    refresh_token: Optional[str] = None

class VerifyTokenRequest(BaseModel):
    token: str
    required_scope: Optional[str] = None
    required_role: Optional[str] = None

class VerifyTokenResponse(BaseModel):
    valid: bool
    username: Optional[str] = None
    role: Optional[str] = None
    roles: List[str] = Field(default_factory=list)
    scopes: List[str] = Field(default_factory=list)
    has_scope: bool = True
    has_role: bool = True
    error: Optional[str] = None
