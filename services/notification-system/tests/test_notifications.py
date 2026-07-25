from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_notification_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_multi_channel_alert_dispatch_latency_sla():
    """
    CRITICAL PRD 5.9 REQUIREMENT TEST:
    Proves multi-channel (SMS, EMAIL, WEBHOOK) emergency alerting with real latency measurement
    confirming the < 2.0 second dispatch SLA requirement.
    """
    payload = {
        "document_id": "DOC-ALERT-SLA-001",
        "patient_id": "PAT-SEPSIS-911",
        "severity": "EMERGENCY",
        "channels": ["SMS", "EMAIL", "WEBHOOK"],
        "alert_message": "CRITICAL EMERGENCY: Sepsis syndrome identified via qSOFA score >= 2. Immediate clinical response required."
    }

    response = client.post("/notify/alert", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    assert data["document_id"] == "DOC-ALERT-SLA-001"
    assert data["severity"] == "EMERGENCY"
    assert len(data["dispatched_channels"]) == 3
    
    channels_sent = [c["channel"] for c in data["dispatched_channels"]]
    assert "SMS" in channels_sent
    assert "EMAIL" in channels_sent
    assert "WEBHOOK" in channels_sent
    
    # SLA LATENCY CHECK: Must be under 2000 ms (< 2.0s)
    latency = data["dispatch_latency_ms"]
    assert latency < 2000.0
    assert data["sla_met"] is True
