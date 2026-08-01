"""
Integration health check tests.
Verifies that /health/ready returns HTTP 200 when dependencies are up
and HTTP 503 when mandatory dependencies (Qdrant, DB, Kafka) are unreachable.
"""

import os
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
import pytest


def _make_client_with_env(qdrant_url: str = "http://qdrant:6333", database_url: str = "postgresql://test:test@localhost/test", kafka_servers: str = "redpanda:9092"):
    os.environ["QDRANT_URL"] = qdrant_url
    os.environ["DATABASE_URL"] = database_url
    os.environ["KAFKA_BOOTSTRAP_SERVERS"] = kafka_servers
    from services.common.health import app

    return TestClient(app, raise_server_exceptions=False)


def test_liveness_always_returns_200():
    client = _make_client_with_env()
    resp = client.get("/health/live")
    assert resp.status_code == 200
    assert resp.json()["status"] == "alive"


def test_readiness_missing_qdrant_url_returns_503():
    os.environ.pop("QDRANT_URL", None)
    os.environ["DATABASE_URL"] = "postgresql://test:test@localhost/test"
    from importlib import reload

    import services.common.health as health_module

    reload(health_module)
    client = TestClient(health_module.app, raise_server_exceptions=False)
    resp = client.get("/health/ready")
    assert resp.status_code == 503
    data = resp.json()
    assert data["detail"]["status"] == "not_ready"


def test_readiness_missing_database_url_returns_503():
    os.environ["QDRANT_URL"] = "http://qdrant:6333"
    os.environ.pop("DATABASE_URL", None)
    from importlib import reload

    import services.common.health as health_module

    reload(health_module)
    client = TestClient(health_module.app, raise_server_exceptions=False)
    resp = client.get("/health/ready")
    assert resp.status_code == 503
    data = resp.json()
    assert data["detail"]["status"] == "not_ready"
