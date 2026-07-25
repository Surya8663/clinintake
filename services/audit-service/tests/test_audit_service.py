import pytest
from fastapi.testclient import TestClient
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.main import app
from src.vault_db import engine, insert_audit_event, AuditVaultRecord, AuditVaultImmutableError

client = TestClient(app)

def test_audit_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_record_and_query_audit_event():
    event_payload = {
        "document_id": "DOC-AUDIT-100",
        "service_name": "document-gateway",
        "event_type": "DOCUMENT_INGESTED",
        "payload": {"file_name": "patient_chart.pdf", "file_size": 2048}
    }
    
    response = client.post("/audit/events", json=event_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["document_id"] == "DOC-AUDIT-100"
    assert "hmac_signature" in data
    assert "entry_hash" in data
    assert data["prev_hash"] is not None

    # Query audit trail
    query_resp = client.get("/audit/events?document_id=DOC-AUDIT-100")
    assert query_resp.status_code == 200
    query_data = query_resp.json()
    assert query_data["total_records"] >= 1
    assert query_data["records"][0]["document_id"] == "DOC-AUDIT-100"

def test_verify_hashchain_integrity():
    response = client.get("/audit/verify")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "intact"
    assert data["total_verified"] >= 1

@pytest.mark.anyio
async def test_audit_vault_update_and_delete_operations_rejected():
    """
    CRITICAL PRD 5.4 REQUIREMENT TEST:
    Proves that any UPDATE or DELETE operation attempted on an existing Audit Vault record
    is strictly REJECTED by raising an AuditVaultImmutableError.
    """
    async with AsyncSession(engine) as session:
        # Create record
        rec = await insert_audit_event(
            session=session,
            event_id="EVT-IMMUTABLE-01",
            document_id="DOC-IMMUTABLE-01",
            service_name="orchestrator",
            event_type="WORKFLOW_STARTED",
            payload={"status": "init"}
        )
        rec_id = rec.id
        assert rec_id is not None

        # 1. Test UPDATE rejection
        rec.event_type = "ILLEGAL_UPDATE_ATTEMPT"
        with pytest.raises(AuditVaultImmutableError) as exc_info_update:
            session.add(rec)
            await session.commit()
            
        assert "Audit Vault records are append-only. UPDATE operations are strictly forbidden" in str(exc_info_update.value)

        # Rollback session state
        await session.rollback()

        # 2. Test DELETE rejection
        result = await session.execute(select(AuditVaultRecord).where(AuditVaultRecord.id == rec_id))
        rec_to_delete = result.scalars().first()
        with pytest.raises(AuditVaultImmutableError) as exc_info_delete:
            await session.delete(rec_to_delete)
            await session.commit()

        assert "Audit Vault records are append-only. DELETE operations are strictly forbidden" in str(exc_info_delete.value)
