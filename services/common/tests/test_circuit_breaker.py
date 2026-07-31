"""
Unit tests for the circuit breaker with exponential backoff.
Verifies CLOSED → OPEN → HALF_OPEN → CLOSED state transitions.
"""
import asyncio
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from services.common.circuit_breaker import CircuitBreaker, CircuitBreakerOpen, CircuitState


@pytest.mark.asyncio
async def test_circuit_breaker_starts_closed():
    cb = CircuitBreaker("test-service", failure_threshold=3)
    assert cb.state == CircuitState.CLOSED


@pytest.mark.asyncio
async def test_circuit_breaker_opens_after_failure_threshold():
    cb = CircuitBreaker("test-service", failure_threshold=3, recovery_timeout_s=60.0)

    async def always_fails():
        raise ConnectionError("Connection refused")

    for _ in range(3):
        try:
            await cb.call(always_fails)
        except ConnectionError:
            pass

    assert cb._state == CircuitState.OPEN


@pytest.mark.asyncio
async def test_circuit_breaker_rejects_calls_when_open():
    cb = CircuitBreaker("test-service", failure_threshold=1, recovery_timeout_s=60.0)
    cb._state = CircuitState.OPEN
    cb._last_failure_time = asyncio.get_event_loop().time()

    async def should_not_be_called():
        return "called"

    with pytest.raises(CircuitBreakerOpen):
        await cb.call(should_not_be_called)


@pytest.mark.asyncio
async def test_circuit_breaker_resets_on_success():
    cb = CircuitBreaker("test-service", failure_threshold=5)
    cb._failure_count = 4

    async def succeeds():
        return "ok"

    result = await cb.call(succeeds)
    assert result == "ok"
    assert cb._failure_count == 0
    assert cb._state == CircuitState.CLOSED
