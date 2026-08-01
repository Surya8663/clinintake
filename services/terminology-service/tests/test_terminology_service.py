from fastapi.testclient import TestClient
import pytest

from src.main import app

client = TestClient(app)


def test_terminology_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["confidence_threshold"] == 0.65


def test_rxnorm_mapping_valid_medication():
    response = client.post("/terminology/map", json={"term": "Lisinopril", "code_system": "RxNorm"})
    assert response.status_code == 200
    data = response.json()
    assert data["is_mapped"] is True
    assert data["requires_unmapped_escalation"] is False
    assert data["code"] is not None
    assert data["confidence_score"] >= 0.65


def test_loinc_mapping_valid_lab():
    response = client.post("/terminology/map", json={"term": "HbA1c", "code_system": "LOINC"})
    assert response.status_code == 200
    data = response.json()
    assert data["is_mapped"] is True
    assert data["code"] == "4548-4"
    assert data["confidence_score"] >= 0.65


def test_snomed_mapping_valid_diagnosis():
    response = client.post("/terminology/map", json={"term": "Essential Hypertension", "code_system": "SNOMED"})
    assert response.status_code == 200
    data = response.json()
    assert data["is_mapped"] is True
    assert data["code"] == "59621000"
    assert data["confidence_score"] >= 0.65


def test_unmapped_obscure_concept_triggers_escalation():
    """
    CRITICAL PRD REQUIREMENT TEST:
    Proves that for an obscure or unmapped clinical concept,
    the service returns requires_unmapped_escalation=True and is_mapped=False.
    """
    response = client.post("/terminology/map", json={"term": "XyzAbcNonExistentCondition9999", "code_system": "SNOMED"})
    assert response.status_code == 200
    data = response.json()
    assert data["is_mapped"] is False
    assert data["requires_unmapped_escalation"] is True
    assert data["code"] is None
    assert data["confidence_score"] < 0.65
