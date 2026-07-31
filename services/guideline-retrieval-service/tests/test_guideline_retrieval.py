from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)

def test_guideline_retrieval_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["relevance_threshold"] == 0.60

def test_valid_guideline_semantic_retrieval():
    response = client.post(
        "/guidelines/retrieve",
        json={
            "query": "prediabetes and type 2 diabetes screening in adults overweight obesity",
            "min_relevance_score": 0.60
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert len(data["matches"]) >= 1
    
    match = data["matches"][0]
    assert match["source"] == "USPSTF"
    assert "Diabetes" in match["section"]
    assert match["clause_id"] == "USPSTF-DM-B"
    assert match["similarity_score"] >= 0.60

def test_metadata_filtering_support():
    response = client.post(
        "/guidelines/retrieve",
        json={
            "query": "screening mammography for women breast cancer",
            "metadata_filter": {"version": "2024-V1"}
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert len(data["matches"]) >= 1
    for m in data["matches"]:
        assert m["version"] == "2024-V1"

def test_insufficient_guideline_evidence_behavior_triggered():
    """
    CRITICAL PRD 5.6 REQUIREMENT TEST:
    Proves that when a query returns no guideline passages above the relevance threshold,
    the service returns status='insufficient_guideline_evidence' and empty matches list,
    and does NOT fall through to a default 'no gap' response.
    """
    irrelevant_query = "orbital space mechanics rocket propulsion trajectories in vacuum"
    
    response = client.post(
        "/guidelines/retrieve",
        json={
            "query": irrelevant_query,
            "min_relevance_score": 0.60
        }
    )
    assert response.status_code == 200
    data = response.json()
    
    # Must return exact status 'insufficient_guideline_evidence'
    assert data["status"] == "insufficient_guideline_evidence"
    assert len(data["matches"]) == 0
    assert data["query"] == irrelevant_query
