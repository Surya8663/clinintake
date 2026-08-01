import os
from pathlib import Path
import sys
from unittest.mock import patch

import pytest

os.environ["QDRANT_URL"] = ":memory:"

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SERVICE_DIR = REPO_ROOT / "services" / "guideline-retrieval-service"

for k in list(sys.modules.keys()):
    if k == "src" or k.startswith("src."):
        del sys.modules[k]

sys.path.insert(0, str(SERVICE_DIR))

from fastapi.testclient import TestClient

from src.main import app
from src.models import GuidelineChunk
from src.qdrant_repository import QdrantUnavailableError, qdrant_repo

client = TestClient(app)


def test_guideline_service_health():
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert "status" in data
    assert data["service"] == "guideline-retrieval-service"
    assert data["qdrant_connected"] is True


def test_qdrant_upsert_and_hybrid_search():
    # 1. Ingest test chunks
    test_chunks = [
        GuidelineChunk(
            chunk_id="TEST-CRC-01",
            guideline_id="USPSTF-CRC-TEST",
            source_organization="USPSTF",
            title="Colorectal Cancer Screening",
            version="2021-V1",
            effective_date="2021-05-18",
            jurisdiction="US",
            section="Colorectal Cancer Screening Guidelines",
            recommendation_strength="Grade A",
            population_tags=["adults", "colorectal_cancer"],
            document_checksum="sha256:testdoc123",
            chunk_checksum="sha256:testchunk123",
            page=1,
            text="The USPSTF recommends screening for colorectal cancer in all adults aged 45 to 75 years using colonoscopy every 10 years.",
            clause_id="USPSTF-CRC-A",
            is_active=True,
        )
    ]

    count = qdrant_repo.upsert_chunks(test_chunks)
    assert count == 1

    # 2. Perform hybrid search
    res = client.post("/guidelines/retrieve", json={"query": "colorectal cancer screening age 45 to 75", "min_relevance_score": 0.01, "metadata_filter": {"jurisdiction": "US"}})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert len(data["matches"]) >= 1
    match = data["matches"][0]
    assert match["clause_id"] == "USPSTF-CRC-A"
    assert "colorectal cancer" in match["passage"].lower()
    assert match["qdrant_point_id"] is not None
    assert match["fusion_method"] == "RRF_HYBRID_COSINE"


def test_empty_results_return_insufficient_guideline_evidence():
    res = client.post(
        "/guidelines/retrieve", json={"query": "nonexistent_condition_unmatched_query_xyz_999", "min_relevance_score": 0.99, "metadata_filter": {"jurisdiction": "NONEXISTENT_JURISDICTION"}}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "insufficient_guideline_evidence"
    assert data["matches"] == []


def test_qdrant_unreachable_returns_503_typed_error():
    with patch.object(qdrant_repo, "search_guidelines", side_effect=QdrantUnavailableError("Qdrant offline")):
        res = client.post("/guidelines/retrieve", json={"query": "diabetes screening"})
        assert res.status_code == 503
        data = res.json()
        assert data["code"] == "GUIDELINE_VECTOR_DB_UNAVAILABLE"
        assert data["retryable"] is True
        assert data["dependency"] == "qdrant"
