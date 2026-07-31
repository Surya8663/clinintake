from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)

def test_guardrail_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_fabricated_clinical_claim_is_blocked_by_guardrail():
    """
    CRITICAL PRD 5.9 REQUIREMENT TEST:
    Proves that a deliberately fabricated claim is detected and BLOCKED by guardrail-service
    (returning blocked=True and is_safe=False), rather than just logging a warning.
    """
    payload = {
        "generated_text": "Patient requires unverified_claim treatment based on fake_citation recommendation.",
        "source_evidence_spans": ["Patient has Type 2 Diabetes Mellitus with HbA1c 8.2%"],
        "guideline_passages": ["USPSTF recommends screening for diabetes in adults aged 35 to 70"]
    }

    response = client.post("/guardrail/verify-grounding", json=payload)
    assert response.status_code == 200
    data = response.json()

    # MUST BE BLOCKED!
    assert data["blocked"] is True
    assert data["is_safe"] is False
    assert len(data["hallucinated_claims"]) > 0
    assert "Guardrail Triggered" in data["reason"] or "Blocked" in data["reason"]

def test_grounded_clinical_claim_passes_guardrail():
    """Proves that grounded clinical text passes the guardrail check."""
    payload = {
        "generated_text": "Patient is overdue for screening per USPSTF Colorectal Cancer 2021 recommendation.",
        "source_evidence_spans": ["Patient screening date 2021-06-15"],
        "guideline_passages": ["USPSTF Colorectal Cancer 2021 recommendation summary"]
    }

    response = client.post("/guardrail/verify-grounding", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["blocked"] is False
    assert data["is_safe"] is True

def test_phi_scrubbing_redacts_sensitive_entities():
    """Proves PHI entity detection and redaction in clinical log text."""
    payload = {
        "raw_text": "Patient Name: John Smith, SSN: 123-45-6789, Phone: (555) 019-2834, Email: john@hospital.org"
    }

    response = client.post("/guardrail/scrub-phi", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["entities_redacted_count"] >= 4
    scrubbed = data["scrubbed_text"]
    assert "John Smith" not in scrubbed
    assert "123-45-6789" not in scrubbed
    assert "[REDACTED_SSN]" in scrubbed
    assert "[REDACTED_PHONE]" in scrubbed
    assert "[REDACTED_EMAIL]" in scrubbed
