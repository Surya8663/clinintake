"""
Shared circuit breaker implementation for all outbound HTTP calls.
Uses exponential backoff with jitter and raises typed errors on failure.
Never catches broad exceptions and continues as success.
"""

import asyncio
from collections.abc import Callable
from enum import StrEnum
import logging
import random
import time
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class CircuitState(StrEnum):
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing - reject calls fast
    HALF_OPEN = "half_open"  # Probing recovery


class CircuitBreakerOpen(Exception):
    """Raised when circuit breaker is open and calls are being rejected."""

    def __init__(self, service_name: str):
        self.service_name = service_name
        super().__init__(f"Circuit breaker OPEN for service '{service_name}'. Outbound call rejected.")


class CircuitBreaker:
    """
    Production circuit breaker with exponential backoff and jitter.
    Integrates with the structured audit event bus on state transitions.
    """

    def __init__(
        self,
        service_name: str,
        failure_threshold: int = 5,
        recovery_timeout_s: float = 30.0,
        half_open_max_calls: int = 2,
    ):
        self.service_name = service_name
        self.failure_threshold = failure_threshold
        self.recovery_timeout_s = recovery_timeout_s
        self.half_open_max_calls = half_open_max_calls

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time: float | None = None
        self._half_open_call_count = 0

    @property
    def state(self) -> CircuitState:
        if self._state == CircuitState.OPEN:
            if time.monotonic() - (self._last_failure_time or 0) >= self.recovery_timeout_s:
                logger.info(f"CircuitBreaker({self.service_name}): Transitioning OPEN -> HALF_OPEN")
                self._state = CircuitState.HALF_OPEN
                self._half_open_call_count = 0
        return self._state

    def _on_success(self):
        self._failure_count = 0
        if self._state != CircuitState.CLOSED:
            logger.info(f"CircuitBreaker({self.service_name}): Transitioning -> CLOSED")
        self._state = CircuitState.CLOSED

    def _on_failure(self):
        self._failure_count += 1
        self._last_failure_time = time.monotonic()
        if self._failure_count >= self.failure_threshold:
            logger.error(f"CircuitBreaker({self.service_name}): Failure threshold reached ({self._failure_count}). Transitioning -> OPEN")
            self._state = CircuitState.OPEN

    async def call(self, fn: Callable, *args, **kwargs) -> Any:
        if self.state == CircuitState.OPEN:
            raise CircuitBreakerOpen(self.service_name)

        if self.state == CircuitState.HALF_OPEN:
            if self._half_open_call_count >= self.half_open_max_calls:
                raise CircuitBreakerOpen(self.service_name)
            self._half_open_call_count += 1

        try:
            result = await fn(*args, **kwargs)
            self._on_success()
            return result
        except Exception:
            self._on_failure()
            raise


async def http_call_with_retry(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    *,
    max_attempts: int = 3,
    base_delay_s: float = 1.0,
    timeout_s: float = 30.0,
    circuit_breaker: CircuitBreaker | None = None,
    **kwargs,
) -> httpx.Response:
    """
    Execute an outbound HTTP call with bounded retry, exponential backoff
    with jitter, timeout, and optional circuit breaker integration.
    Never catches exceptions silently.
    """
    last_exc: Exception | None = None

    for attempt in range(1, max_attempts + 1):
        try:

            async def _do_request():
                return await client.request(method, url, timeout=timeout_s, **kwargs)

            if circuit_breaker:
                response = await circuit_breaker.call(_do_request)
            else:
                response = await _do_request()

            return response

        except (httpx.TimeoutException, httpx.ConnectError) as exc:
            last_exc = exc
            if attempt < max_attempts:
                delay = base_delay_s * (2 ** (attempt - 1)) + random.uniform(0, 0.5)
                logger.warning(f"HTTP call to {url} failed (attempt {attempt}/{max_attempts}): {exc}. " f"Retrying in {delay:.2f}s...")
                await asyncio.sleep(delay)
            else:
                logger.exception(f"HTTP call to {url} exhausted all {max_attempts} retry attempts.")
                raise

        except CircuitBreakerOpen:
            raise

    raise last_exc  # type: ignore
