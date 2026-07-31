"""
Idempotency key store backed by Redis with TTL.
Used to prevent duplicate EHR writes, duplicate audit events, and duplicate DLQ entries.
Redis is ephemeral only - idempotency keys are short-lived and not treated as durable clinical records.
"""
import hashlib
import logging

import redis.asyncio as aioredis

logger = logging.getLogger(__name__)

IDEMPOTENCY_TTL_SECONDS = 86400  # 24 hours


class IdempotencyStore:
    """
    Redis-backed idempotency store for preventing duplicate side effects.
    Keys expire after TTL. Not suitable for long-term durable state.
    """

    def __init__(self, redis_client: aioredis.Redis, namespace: str = "clinintake:idempotency"):
        self._redis = redis_client
        self._namespace = namespace

    def _key(self, idempotency_id: str) -> str:
        safe = hashlib.sha256(idempotency_id.encode()).hexdigest()
        return f"{self._namespace}:{safe}"

    async def is_duplicate(self, idempotency_id: str) -> bool:
        """Returns True if this idempotency key has already been processed."""
        key = self._key(idempotency_id)
        exists = await self._redis.exists(key)
        return bool(exists)

    async def mark_processed(self, idempotency_id: str, metadata: str = "") -> None:
        """Marks an idempotency key as processed with TTL. Raises on Redis error."""
        key = self._key(idempotency_id)
        await self._redis.setex(key, IDEMPOTENCY_TTL_SECONDS, metadata or "processed")
        logger.info(f"Idempotency key registered for {idempotency_id[:16]}... (TTL={IDEMPOTENCY_TTL_SECONDS}s)")

    async def check_and_mark(self, idempotency_id: str, metadata: str = "") -> bool:
        """
        Atomically check and mark an idempotency key.
        Returns True if this is a duplicate (already processed).
        Returns False and marks if this is the first time.
        """
        key = self._key(idempotency_id)
        # SET NX (only if not exists) with TTL
        result = await self._redis.set(
            key, metadata or "processed",
            nx=True,
            ex=IDEMPOTENCY_TTL_SECONDS
        )
        if result is None:
            logger.warning(f"Duplicate idempotency key detected for {idempotency_id[:16]}...")
            return True  # Duplicate
        return False  # First time
