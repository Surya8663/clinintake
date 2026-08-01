from unittest.mock import patch

from fastapi.testclient import TestClient
import pytest

from src.main import app

client = TestClient(app)


def test_care_gap_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_empty_guideline_evidence_returns_insufficient_evidence():
    """Empty guideline_passages returns summary='Insufficient guideline evidence' and generation_mode='insufficient_evidence'."""
    pkg = {
        "document_id": "DOC-NO-PASSAGES-01",
        "patient_id": "PAT-NO-PASSAGES",
        "temporal_care_gaps": [{"measure_name": "Colorectal Cancer Screening", "status": "overdue", "due_date": "2025-06-15"}],
        "guideline_passages": [],
    }

    response = client.post("/care-gap/explain", json=pkg)
    assert response.status_code == 200
    data = response.json()
    assert data["document_id"] == "DOC-NO-PASSAGES-01"
    assert data["explanation_summary"] == "Insufficient guideline evidence"
    assert data["generation_mode"] == "insufficient_evidence"
    assert data["cited_guideline_passages"] == []
