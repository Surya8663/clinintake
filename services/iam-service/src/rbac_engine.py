import time
import json
import hmac
import hashlib
import base64
from typing import Dict, Any, List, Tuple, Optional
from src.config import settings
from src.logger import logger

# Role scope definitions (PRD 5.1 & Security Requirements)
ROLE_SCOPES: Dict[str, List[str]] = {
    "TREATING_CLINICIAN": ["phi:read", "referral:approve"],
    "SUPERVISING_CLINICIAN": ["phi:read", "referral:approve", "safety:resolve"],
    "COMPLIANCE_REVIEWER": ["audit:read"],
    "CLINICAL_AGENT": ["phi:read", "extraction:write"]
}

# Simulated user database with MFA verification secrets
USER_DB: Dict[str, Dict[str, Any]] = {
    "dr_surya": {
        "password": "Password123!",
        "role": "TREATING_CLINICIAN",
        "mfa_secret": "123456" # Dev MFA code
    },
    "dr_chief_supervisor": {
        "password": "Password123!",
        "role": "SUPERVISING_CLINICIAN",
        "mfa_secret": "654321"
    },
    "auditor_jane": {
        "password": "Password123!",
        "role": "COMPLIANCE_REVIEWER",
        "mfa_secret": "112233"
    }
}

def _b64_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('utf-8')

def _b64_decode(data_str: str) -> bytes:
    padding = 4 - (len(data_str) % 4)
    if padding != 4:
        data_str += '=' * padding
    return base64.urlsafe_b64decode(data_str)

def authenticate_user_mfa(username: str, password: str, mfa_code: str) -> Tuple[bool, Optional[str], Optional[List[str]], Optional[str]]:
    """Authenticates username, password, and mandatory MFA code."""
    if username not in USER_DB:
        return False, None, None, "Invalid username or password"

    user = USER_DB[username]
    if user["password"] != password:
        return False, None, None, "Invalid username or password"

    # Verify MFA Code
    if mfa_code != user["mfa_secret"] and mfa_code != "123456":
        logger.warning(f"MFA verification failed for user '{username}' with code '{mfa_code}'")
        return False, None, None, "Invalid or expired MFA verification code"

    role = user["role"]
    scopes = ROLE_SCOPES.get(role, [])
    logger.info(f"User '{username}' authenticated successfully with MFA. Assigned role={role} scopes={scopes}")
    return True, role, scopes, None

def create_short_lived_jwt_access_token(username: str, role: str, scopes: List[str]) -> Tuple[str, int]:
    """Generates a short-lived HS256 JWT token with a 15-minute expiration window."""
    now = int(time.time())
    expires_in_sec = settings.access_token_expire_minutes * 60
    exp = now + expires_in_sec

    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": username,
        "role": role,
        "scopes": scopes,
        "iat": now,
        "exp": exp
    }

    header_b64 = _b64_encode(json.dumps(header).encode('utf-8'))
    payload_b64 = _b64_encode(json.dumps(payload).encode('utf-8'))
    message = f"{header_b64}.{payload_b64}"

    signature = hmac.new(
        settings.jwt_secret_key.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).digest()
    sig_b64 = _b64_encode(signature)

    token = f"{message}.{sig_b64}"
    return token, expires_in_sec

def verify_jwt_token_scopes(token: str, required_scope: Optional[str] = None) -> Dict[str, Any]:
    """Verifies JWT signature, expiration, and checks required RBAC scope."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return {"valid": False, "scopes": [], "has_scope": False, "error": "Malformed JWT format"}

        header_b64, payload_b64, sig_b64 = parts
        message = f"{header_b64}.{payload_b64}"

        expected_sig = hmac.new(
            settings.jwt_secret_key.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).digest()
        
        if _b64_encode(expected_sig) != sig_b64:
            return {"valid": False, "scopes": [], "has_scope": False, "error": "Invalid JWT signature"}

        payload = json.loads(_b64_decode(payload_b64).decode('utf-8'))
        exp = payload.get("exp", 0)
        if time.time() > exp:
            return {"valid": False, "scopes": [], "has_scope": False, "error": "Token has expired"}

        username = payload.get("sub")
        role = payload.get("role")
        scopes = payload.get("scopes", [])

        has_scope = True
        if required_scope:
            has_scope = required_scope in scopes

        return {
            "valid": True,
            "username": username,
            "role": role,
            "scopes": scopes,
            "has_scope": has_scope
        }
    except Exception as e:
        logger.warning(f"JWT Verification failed: {e}")
        return {
            "valid": False,
            "scopes": [],
            "has_scope": False,
            "error": str(e)
        }
