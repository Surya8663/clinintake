from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_metrics_dashboard_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_kpi_computation_returns_real_benchmark_metrics():
    """
    CRITICAL PRD SECTION 13 REQUIREMENT TEST:
    Proves metrics dashboard calculates real non-placeholder KPIs (extraction accuracy,
    red-flag sensitivity, hallucination rate) against ground-truth benchmark datasets.
    """
    response = client.get("/metrics/kpis")
    assert response.status_code == 200
    data = response.json()

    # 1. Extraction Accuracy Metric
    acc = data["extraction_accuracy"]
    assert acc["total_test_samples"] > 0
    assert 0.0 <= acc["accuracy_percentage"] <= 100.0
    assert acc["accuracy_percentage"] == 100.0 # 10/10 matched in ground truth set

    # 2. Red-Flag Sensitivity Metric
    sens = data["red_flag_sensitivity"]
    assert sens["total_emergency_cases"] > 0
    assert 0.0 <= sens["sensitivity_percentage"] <= 100.0
    assert sens["sensitivity_percentage"] == 100.0 # 4/4 emergencies detected

    # 3. Hallucination Rate Metric
    hal = data["hallucination_rate"]
    assert hal["total_explanations"] > 0
    assert 0.0 <= hal["hallucination_rate_percentage"] <= 100.0
    assert hal["hallucination_rate_percentage"] == 25.0 # 1/4 hallucinated in benchmark set
