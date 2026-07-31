import os
os.environ["QDRANT_URL"] = ":memory:"

from fastapi.testclient import TestClient
import pytest

from src.config import settings
settings.qdrant_url = ":memory:"

from src.main import app
from src.models import GuidelineChunk
from src.qdrant_repository import qdrant_repo

client = TestClient(app)


@pytest.fixture(autouse=True, scope="module")
def setup_test_qdrant():
    qdrant_repo._client = None
    chunks = [
        GuidelineChunk(
            chunk_id="USPSTF-DM-01",
            guideline_id="USPSTF-DM-2021",
            source_organization="USPSTF",
            title="Screening for Diabetes",
            version="2024-V1",
            effective_date="2021-08-24",
            jurisdiction="US",
            section="Diabetes Screening",
            clause_id="USPSTF-DM-B",
            text="prediabetes and type 2 diabetes screening in adults overweight obesity",
            chunk_checksum="chk001",
            document_checksum="docchk001"
        ),
        GuidelineChunk(
            chunk_id="USPSTF-MAMMO-01",
            guideline_id="USPSTF-BC-2024",
            source_organization="USPSTF",
            title="Screening Mammography",
            version="2024-V1",
            effective_date="2024-04-30",
            jurisdiction="US",
            section="Breast Cancer Screening",
            clause_id="USPSTF-BC-A",
            text="screening mammography for women breast cancer",
            chunk_checksum="chk002",
            document_checksum="docchk002"
        ),
    ]
    qdrant_repo.upsert_chunks(chunks)


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
