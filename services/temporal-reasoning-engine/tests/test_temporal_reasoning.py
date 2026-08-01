from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)


def test_temporal_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_state_1_overdue():
    """Output State 1: OVERDUE (Last screening 24 months ago for 12-month interval)."""
    response = client.post(
        "/temporal/evaluate",
        json={"procedure_name": "HbA1c_Testing", "last_screening_date": "2024-01-15", "patient_age": 55, "risk_category": "average", "guideline_interval_months": 12, "reference_date": "2026-01-15"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "overdue"
    assert data["months_since_last_screening"] >= 24.0


def test_state_2_due():
    """Output State 2: DUE (Last screening 12 months ago for 12-month interval)."""
    response = client.post(
        "/temporal/evaluate",
        json={"procedure_name": "Colonoscopy", "last_screening_date": "2025-01-15", "patient_age": 50, "risk_category": "average", "guideline_interval_months": 12, "reference_date": "2026-01-15"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "due"


def test_state_3_not_due():
    """Output State 3: NOT-DUE (Last screening 3 months ago for 12-month interval)."""
    response = client.post(
        "/temporal/evaluate",
        json={"procedure_name": "Mammogram", "last_screening_date": "2025-10-15", "patient_age": 52, "risk_category": "average", "guideline_interval_months": 12, "reference_date": "2026-01-15"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "not-due"


def test_state_4_insufficient_information_missing_date():
    """Output State 4: INSUFFICIENT-INFORMATION (Missing last screening date)."""
    response = client.post(
        "/temporal/evaluate",
        json={"procedure_name": "Colonoscopy", "last_screening_date": None, "patient_age": 60, "risk_category": "average", "guideline_interval_months": 12, "reference_date": "2026-01-15"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "insufficient-information"
    assert data["next_due_date"] is None


def test_state_4_insufficient_information_missing_age():
    """Output State 4: INSUFFICIENT-INFORMATION (Missing age boundary)."""
    response = client.post(
        "/temporal/evaluate",
        json={"procedure_name": "Colonoscopy", "last_screening_date": "2024-05-10", "patient_age": None, "risk_category": "average", "guideline_interval_months": 12, "reference_date": "2026-01-15"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "insufficient-information"
