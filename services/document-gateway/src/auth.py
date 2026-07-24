import jwt
from fastapi import Header, HTTPException, status
from src.config import settings
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
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=["HS256"]
        )
        logger.info(f"JWT verified successfully for user: {payload.get('sub', 'unknown')}")
        return payload
    except jwt.PyJWTError as e:
        logger.warning(f"JWT signature verification failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication token: {str(e)}"
        )
