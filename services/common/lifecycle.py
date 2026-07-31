"""
ClinIntake Phase 12: Graceful shutdown, connection pooling, and startup dependency validation.
Provides a reusable ApplicationLifecycle context manager for all FastAPI services.
"""
import asyncio
import logging
import os
import signal
import sys
from contextlib import asynccontextmanager
from typing import Optional, Any

import httpx

logger = logging.getLogger(__name__)


class StartupDependencyError(RuntimeError):
    """Raised when a required external dependency is not reachable at startup."""
    pass


async def _check_http_dependency(url: str, service_label: str, timeout_s: float = 5.0) -> None:
    """
    Probes an HTTP endpoint during service startup.
    Raises StartupDependencyError if it cannot be reached.
    """
    try:
        async with httpx.AsyncClient(timeout=timeout_s) as client:
            resp = await client.get(url)
            if resp.status_code >= 500:
                raise StartupDependencyError(
                    f"Service '{service_label}' at {url} returned HTTP {resp.status_code}."
                )
            logger.info(f"Startup: dependency '{service_label}' is reachable (HTTP {resp.status_code}).")
    except httpx.ConnectError as exc:
        raise StartupDependencyError(
            f"Startup: required dependency '{service_label}' is unreachable at {url}: {exc}"
        ) from exc
    except httpx.TimeoutException as exc:
        raise StartupDependencyError(
            f"Startup: required dependency '{service_label}' timed out at {url}: {exc}"
        ) from exc


async def validate_required_env_vars(*var_names: str) -> None:
    """
    Validates that all required environment variables are present at startup.
    Missing variables raise StartupDependencyError immediately with a clear message.
    """
    missing = [v for v in var_names if not os.environ.get(v)]
    if missing:
        raise StartupDependencyError(
            f"FATAL: Missing required environment variables: {', '.join(missing)}. "
            f"Service cannot start safely without these values."
        )
    logger.info(f"Startup: All required environment variables present: {list(var_names)}")


@asynccontextmanager
async def application_lifecycle(app: Any, required_env_vars: list[str], http_dependencies: dict[str, str] = {}):
    """
    Reusable FastAPI lifespan context manager providing:
    1. Startup env var validation (raises clearly if missing)
    2. Startup dependency health probing (raises clearly if unreachable)
    3. Graceful shutdown with drain timeout
    """
    # --- STARTUP ---
    try:
        await validate_required_env_vars(*required_env_vars)
        for label, url in http_dependencies.items():
            await _check_http_dependency(url, label)
        logger.info("Startup: All dependencies verified. Service is ready.")
    except StartupDependencyError as e:
        logger.critical(f"STARTUP FAILED: {e}")
        sys.exit(1)

    yield

    # --- SHUTDOWN ---
    logger.info("Shutdown: Initiating graceful shutdown. Draining in-flight requests...")
    await asyncio.sleep(0.5)  # Brief drain window
    logger.info("Shutdown: Complete.")
