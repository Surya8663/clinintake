from fastapi import Header, HTTPException, status

from services.common.jwt_verifier import decode_and_verify_jwt
from src.logger import logger


def verify_jwt_token(authorization: str = Header(...)) -> dict:
    if not authorization.startswith("Bearer "):
        logger.warning("Invalid authorization header format received")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication. Bearer token expected."
        )
    
    token = authorization.split(" ")[1]
    try:
        claims = decode_and_verify_jwt(token)
        logger.info(f"JWT verified successfully for user: {claims.get('sub', 'unknown')}")
        return claims
    except HTTPException as e:
        logger.warning(f"JWT verification failed: {e.detail}")
        raise e
    except Exception as e:
        logger.warning(f"JWT signature verification failed: {e!s}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication token: {e!s}"
        )
