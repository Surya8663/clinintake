import json
from typing import Tuple, Optional, Dict, Any
from src.config import settings
from src.logger import logger

# Local memory store fallback for test environments when Redis container is offline
_LOCAL_IDEMPOTENCY_CACHE: Dict[str, Dict[str, Any]] = {}

def check_and_set_idempotency_key(idempotency_key: str, response_data: Optional[Dict[str, Any]] = None) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """
    Redis-backed (with local cache fallback) idempotency key checker.
    Returns (is_duplicate: bool, previous_response: Optional[dict]).
    """
    key = f"fhir_idempotency:{idempotency_key}"
    
    # Check local cache fallback first for unit testing
    if key in _LOCAL_IDEMPOTENCY_CACHE:
        logger.info(f"Idempotency cache hit! Key '{idempotency_key}' already processed. Suppressing duplicate write.")
        return True, _LOCAL_IDEMPOTENCY_CACHE[key]

    try:
        import redis
        r = redis.Redis(host=settings.redis_host, port=settings.redis_port, db=0, socket_timeout=0.5)
        existing = r.get(key)
        if existing:
            data = json.loads(existing.decode('utf-8'))
            logger.info(f"Redis Idempotency Hit for key='{idempotency_key}'. Returning cached no-op response.")
            return True, data
        
        if response_data is not None:
            r.setex(key, 86400, json.dumps(response_data)) # 24h TTL
            _LOCAL_IDEMPOTENCY_CACHE[key] = response_data
            return False, None
    except Exception as e:
        logger.debug(f"Redis fallback to memory cache ({e})")
        if response_data is not None:
            _LOCAL_IDEMPOTENCY_CACHE[key] = response_data
            
    return False, None
