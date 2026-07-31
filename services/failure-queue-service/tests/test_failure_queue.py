from fastapi.testclient import TestClient
import pytest
from src.database import engine
from src.main import app
from src.models import Base

@pytest.fixture(autouse=True)
def setup_test_db():
    import asyncio
    async def create_tables():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    asyncio.run(create_tables())

client = TestClient(app)

def test_failure_queue_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_retry_exhaustion_escalates_to_manual_review():
    """
    CRITICAL PRD 5.9 REQUIREMENT TEST:
    Proves that retry count is tracked and that after retries are exhausted (>= max_retries),
    the item status transitions to 'manual_review' in the dead-letter queue.
    """
    doc_id = "DOC-EXHAUST-RETRY-999"
    payload = {
        "document_id": doc_id,
        "service_name": "extraction-agent",
        "error_type": "LOW_CONFIDENCE_EXTRACTION",
        "error_message": "Confidence score 0.42 below required threshold 0.70"
    }

    # 1. Enqueue 1st failure (retry_count=0)
    resp1 = client.post("/failure/enqueue", json=payload)
    assert resp1.status_code == 200
    assert resp1.json()["retry_count"] == 0
    assert resp1.json()["status"] == "queued"

    # 2. Enqueue 2nd failure (retry_count=1)
    resp2 = client.post("/failure/enqueue", json=payload)
    assert resp2.status_code == 200
    assert resp2.json()["retry_count"] == 1

    # 3. Enqueue 3rd failure (retry_count=2)
    resp3 = client.post("/failure/enqueue", json=payload)
    assert resp3.status_code == 200
    assert resp3.json()["retry_count"] == 2

    # 4. Enqueue 4th failure (retry_count=3 -> Exhausted!)
    resp4 = client.post("/failure/enqueue", json=payload)
    assert resp4.status_code == 200
    data4 = resp4.json()
    assert data4["retry_count"] == 3
    assert data4["status"] == "manual_review"

    # 5. Check DLQ summary endpoint
    dlq_resp = client.get("/failure/dlq")
    assert dlq_resp.status_code == 200
    dlq_data = dlq_resp.json()
    assert dlq_data["manual_review_items"] >= 1
