import os
import time, json, hmac, hashlib
from fastapi.testclient import TestClient

os.environ["JWT_SECRET_KEY"] = "test_metrics_secret_key_2026"

from src.main import app
from services.common.jwt_verifier import _b64_encode

client = TestClient(app)

def get_auth_header():
    now = int(time.time())
    exp = now + 900
    roles = ["quality:metrics:read"]
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": "quality_reviewer",
        "preferred_username": "quality_reviewer",
        "role": "QUALITY_REVIEWER",
        "roles": roles,
        "realm_access": {"roles": roles},
        "scopes": roles,
        "scope": " ".join(roles),
        "iss": "http://localhost:8085/realms/clinintake",
        "aud": "clinintake-bff",
        "iat": now,
        "exp": exp
    }
    header_b64 = _b64_encode(json.dumps(header).encode('utf-8'))
    payload_b64 = _b64_encode(json.dumps(payload).encode('utf-8'))
    message = f"{header_b64}.{payload_b64}"
    sig = hmac.new(b"test_metrics_secret_key_2026", message.encode('utf-8'), hashlib.sha256).digest()
    token = f"{message}.{_b64_encode(sig)}"
    return {"Authorization": f"Bearer {token}"}

def test_metrics_dashboard_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_kpi_computation_returns_real_benchmark_metrics():
    headers = get_auth_header()
    response = client.get("/metrics/kpis", headers=headers)
    assert response.status_code == 200
    data = response.json()

    # 1. Extraction Accuracy Metric
    acc = data["extraction_accuracy"]
    assert acc["total_test_samples"] > 0
    assert 0.0 <= acc["accuracy_percentage"] <= 100.0
    assert acc["accuracy_percentage"] == 100.0

    # 2. Red-Flag Sensitivity Metric
    sens = data["red_flag_sensitivity"]
    assert sens["total_emergency_cases"] > 0
    assert 0.0 <= sens["sensitivity_percentage"] <= 100.0
    assert sens["sensitivity_percentage"] == 100.0

    # 3. Hallucination Rate Metric
    hal = data["hallucination_rate"]
    assert hal["total_explanations"] > 0
    assert 0.0 <= hal["hallucination_rate_percentage"] <= 100.0
    assert hal["hallucination_rate_percentage"] == 25.0
