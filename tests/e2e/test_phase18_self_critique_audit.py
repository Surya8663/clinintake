import os
import sys
import importlib
import pytest
from fastapi.testclient import TestClient

def _load_service_app(service_name: str):
    service_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "services", service_name))
    for mod in list(sys.modules.keys()):
        if mod == "src" or mod.startswith("src."):
            del sys.modules[mod]

    if service_dir not in sys.path:
        sys.path.insert(0, service_dir)

    main_mod = importlib.import_module("src.main")
    if service_dir in sys.path:
        sys.path.remove(service_dir)
    return main_mod.app

def test_pessimistic_safety_incomplete_when_vitals_missing():
    """
    PHASE 18 CRITICAL SAFETY TEST:
    Proves that if any required vital measurement is missing, the safety assessment MUST NOT
    default to a "safe" score, but instead return status="incomplete" and
    rationale="Safety assessment incomplete — required clinical measurements unavailable".
    """
    safety_app = _load_service_app("safety-sub-agent")
    client = TestClient(safety_app)

    # Payload missing respiratory_rate and spo2
    payload = {
        "document_id": "DOC-MISSING-VITALS-001",
        "vitals": {
            "systolic_bp": 120,
            "heart_rate": 72
        }
    }

    response = client.post("/safety/evaluate", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["assessment_status"] == "incomplete"
    assert data["news2_score"] is None
    assert data["qsofa_score"] is None
    assert "Safety assessment incomplete — required clinical measurements unavailable" in data["rationale"]
    assert data["is_emergency"] is False

def test_misspelled_drug_term_fuzzy_resolution():
    """
    PHASE 18 ADVERSARIAL TERMINOLOGY TEST:
    Proves that misspelled drug names (e.g. 'metformn', 'lisinoprl') are resolved via fuzzy terminology index matching.
    """
    term_app = _load_service_app("terminology-service")
    client = TestClient(term_app)

    response = client.post("/terminology/map", json={"term": "metformn 500mg", "code_system": "RxNorm"})
    assert response.status_code == 200
    data = response.json()

    assert data["is_mapped"] is True
    assert data["code"] == "860975" # RxNorm Metformin
    assert data["confidence_score"] >= 0.75
    assert data["source_api"] == "RxNorm_Fuzzy_Index"

def test_no_matching_guideline_returns_insufficient_evidence_status():
    """
    PHASE 18 EDGE-CASE GUIDELINE TEST:
    Proves that a guideline query with no matching guideline above threshold returns
    status="insufficient_guideline_evidence" rather than fabricating or returning irrelevant passages.
    """
    guide_app = _load_service_app("guideline-retrieval-service")
    client = TestClient(guide_app)

    response = client.post("/guidelines/retrieve", json={"query": "rare genetic mitochondrial mutation syndrome management"})
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "insufficient_guideline_evidence"
    assert len(data["matches"]) == 0

def test_hallucinated_claim_is_blocked_by_guardrail():
    """
    PHASE 18 HALLUCINATION GUARDRAIL TEST:
    Proves that an ungrounded or fabricated claim is detected and BLOCKED by guardrail-service.
    """
    guard_app = _load_service_app("guardrail-service")
    client = TestClient(guard_app)

    payload = {
        "generated_text": "Patient requires unverified_claim treatment based on fake_citation recommendation.",
        "source_evidence_spans": ["Patient has Type 2 Diabetes Mellitus with HbA1c 8.2%"],
        "guideline_passages": ["USPSTF recommends screening for diabetes in adults aged 35 to 70"]
    }

    response = client.post("/guardrail/verify-grounding", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["blocked"] is True
    assert data["is_safe"] is False
    assert len(data["hallucinated_claims"]) > 0

def test_all_service_thresholds_are_config_backed():
    """
    PHASE 18 CONFIGURATION AUDIT TEST:
    Proves that critical thresholds across services are backed by Pydantic BaseSettings objects.
    """
    # 1. Extraction Agent settings
    ext_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "services", "extraction-agent"))
    for mod in list(sys.modules.keys()):
        if mod == "src" or mod.startswith("src."):
            del sys.modules[mod]
    sys.path.insert(0, ext_dir)
    from src.config import settings as ext_settings
    assert hasattr(ext_settings, "confidence_threshold")
    assert ext_settings.confidence_threshold == 0.7
    sys.path.remove(ext_dir)

    # 2. Guideline Retrieval settings
    guide_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "services", "guideline-retrieval-service"))
    for mod in list(sys.modules.keys()):
        if mod == "src" or mod.startswith("src."):
            del sys.modules[mod]
    sys.path.insert(0, guide_dir)
    from src.config import settings as guide_settings
    assert hasattr(guide_settings, "relevance_threshold")
    assert guide_settings.relevance_threshold == 0.60
    sys.path.remove(guide_dir)

    # 3. Terminology Service settings
    term_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "services", "terminology-service"))
    for mod in list(sys.modules.keys()):
        if mod == "src" or mod.startswith("src."):
            del sys.modules[mod]
    sys.path.insert(0, term_dir)
    from src.config import settings as term_settings
    assert hasattr(term_settings, "confidence_threshold")
    assert term_settings.confidence_threshold == 0.65
    sys.path.remove(term_dir)
