import datetime
from unittest.mock import patch

from fastapi.testclient import TestClient
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Configure testing DB engine override BEFORE importing main app engine
from src.config import settings

settings.database_url = "sqlite+aiosqlite:///:memory:"

from src.database import async_session
from src.main import app
from src.models import Base, Patient, QuarantineRecord

client = TestClient(app)


@pytest_asyncio.fixture(autouse=True)
async def setup_test_db():
    from src.database import engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        # Seed testing demographic records
        session.add_all(
            [
                Patient(id="PAT-001", first_name="John", last_name="Doe", date_of_birth=datetime.date(1980, 1, 1), gender="Male"),
                Patient(id="PAT-002", first_name="Jane", last_name="Smith", date_of_birth=datetime.date(1992, 5, 15), gender="Female"),
                Patient(id="PAT-003", first_name="Alice", last_name="Williams", date_of_birth=datetime.date(1975, 9, 30), gender="Female"),
            ]
        )
        await session.commit()
    yield


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "patient-identity-service"}


def test_exact_match_resolves_instantly():
    # Attempting match for John Doe with exact details
    response = client.post("/identity/resolve", json={"document_id": "doc-exact-123", "first_name": "John", "last_name": "Doe", "date_of_birth": "1980-01-01"})
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["status"] == "resolved"
    assert res_data["patient_id"] == "PAT-001"
    assert res_data["confidence_score"] == 1.0


def test_fuzzy_match_resolves_successfully():
    # Attempting match with slight name typo (Jonh Doee) but correct DOB
    response = client.post("/identity/resolve", json={"document_id": "doc-fuzzy-123", "first_name": "Jonh", "last_name": "Doee", "date_of_birth": "1980-01-01"})
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["status"] == "resolved"
    assert res_data["patient_id"] == "PAT-001"
    # Name similarity will be slightly lower than 1.0 but DOB exact match gives it > threshold
    assert res_data["confidence_score"] > settings.patient_match_threshold


def test_low_confidence_quarantines_and_halts():
    # Attempting match with correct name but incorrect DOB (overall score is low)
    response = client.post("/identity/resolve", json={"document_id": "doc-low-conf-123", "first_name": "John", "last_name": "Doe", "date_of_birth": "1985-06-15"})
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["status"] == "quarantined"
    assert res_data["confidence_score"] < settings.patient_match_threshold

    # Assert that this document was added to the quarantine queue table
    quarantine_list_resp = client.get("/identity/quarantine")
    assert quarantine_list_resp.status_code == 200
    quarantine_items = quarantine_list_resp.json()
    assert len(quarantine_items) == 1
    assert quarantine_items[0]["document_id"] == "doc-low-conf-123"
    assert quarantine_items[0]["status"] == "pending_review"


def test_unmatched_demographics_quarantines_and_halts():
    # Completely unknown patient
    response = client.post("/identity/resolve", json={"document_id": "doc-unknown-999", "first_name": "Robert", "last_name": "Plant", "date_of_birth": "1948-08-20"})
    assert response.status_code == 200
    assert response.json()["status"] == "quarantined"

    # Verify quarantine database contents
    quarantine_list_resp = client.get("/identity/quarantine")
    assert len(quarantine_list_resp.json()) == 1
    assert quarantine_list_resp.json()[0]["document_id"] == "doc-unknown-999"


def test_manual_resolution_clears_quarantine():
    # 1. Trigger quarantine for unknown patient
    response_resolve = client.post("/identity/resolve", json={"document_id": "doc-man-res", "first_name": "Janee", "last_name": "Smithe", "date_of_birth": "1990-12-12"})
    assert response_resolve.json()["status"] == "quarantined"

    # 2. Check pending queue contains it
    q_items_before = client.get("/identity/quarantine").json()
    assert len(q_items_before) == 1

    # 3. Manually map it to Jane Smith (PAT-002)
    resolve_resp = client.post("/identity/quarantine/doc-man-res/resolve", json={"patient_id": "PAT-002"})
    assert resolve_resp.status_code == 200
    assert resolve_resp.json()["status"] == "success"

    # 4. Assert queue is now empty
    q_items_after = client.get("/identity/quarantine").json()
    assert len(q_items_after) == 0
