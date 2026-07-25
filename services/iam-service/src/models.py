from pydantic import BaseModel, Field
from typing import List, Optional

class LoginRequest(BaseModel):
    username: str
    password: str
    mfa_code: str = Field(..., description="Mandatory MFA 6-digit verification code")

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_seconds: int = 900 # 15 minutes
    role: str
    scopes: List[str]

class VerifyTokenRequest(BaseModel):
    token: str
    required_scope: Optional[str] = None

class VerifyTokenResponse(BaseModel):
    valid: bool
    username: Optional[str] = None
    role: Optional[str] = None
    scopes: List[str] = Field(default_factory=list)
    has_scope: bool = True
    error: Optional[str] = None
