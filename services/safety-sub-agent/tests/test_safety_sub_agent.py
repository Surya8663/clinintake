from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)

def test_safety_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_emergency_sepsis_detection_high_news2():
    response = client.post(
        "/safety/evaluate",
        json={
            "document_id": "DOC-EMERGENCY-01",
            "vitals": {
                "respiratory_rate": 26, # 3 pts
                "spo2": 89.0,            # 3 pts
                "uses_supplemental_oxygen": True, # 2 pts
                "systolic_bp": 85,       # 3 pts
                "heart_rate": 135,       # 3 pts
                "consciousness_level": "Confusion", # 3 pts
                "temperature": 39.5
            },
            "clinical_text": "Patient presenting with fever, hypotension, and altered mental state."
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_emergency"] is True
    assert data["assessment_status"] == "complete"
    assert data["news2_score"] >= 7
    assert data["qsofa_score"] >= 2
    assert len(data["red_flags"]) >= 1
    assert any(rf["syndrome"] == "sepsis" for rf in data["red_flags"])

def test_redflags_detection_stroke_and_chest_pain():
    response = client.post(
        "/safety/evaluate",
        json={
            "document_id": "DOC-EMERGENCY-02",
            "clinical_text": "Patient with sudden facial droop, slurred speech, and acute crushing chest pain.",
            "symptoms": ["chest pain", "facial droop"]
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_emergency"] is True
    syndromes = [rf["syndrome"] for rf in data["red_flags"]]
    assert "stroke" in syndromes
    assert "chest_pain" in syndromes

def test_pessimistic_safety_missing_required_vital_returns_incomplete():
    """
    CRITICAL PRD PESSIMISTIC SAFETY REQUIREMENT TEST:
    Proves that if a required vital measurement (e.g. respiratory_rate) is missing,
    the service returns assessment_status='incomplete' and exact rationale:
    'Safety assessment incomplete — required clinical measurements unavailable'
    and does NOT default to a safe score.
    """
    response = client.post(
        "/safety/evaluate",
        json={
            "document_id": "DOC-INCOMPLETE-03",
            "vitals": {
                "respiratory_rate": None, # Missing required respiratory rate!
                "spo2": 98.0,
                "systolic_bp": 120,
                "heart_rate": 72
            },
            "clinical_text": "Routine checkup."
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["assessment_status"] == "incomplete"
    assert data["news2_score"] is None
    assert data["qsofa_score"] is None
    assert "Safety assessment incomplete — required clinical measurements unavailable" in data["rationale"]
