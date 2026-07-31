import hashlib
import hmac
import json
import os
import time

from fastapi.testclient import TestClient
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

os.environ["HMAC_SECRET_KEY"] = "test_audit_hmac_key_2026"
os.environ["JWT_SECRET_KEY"] = "test_audit_jwt_secret_2026"

from services.common.jwt_verifier import _b64_encode
from src.main import app
from src.vault_db import AuditVaultImmutableError, AuditVaultRecord, Base, engine, insert_audit_event

client = TestClient(app)

@pytest.fixture(autouse=True, scope="module")
def reset_db():
    import asyncio
    async def _reset():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
    asyncio.run(_reset())

def get_auth_header(roles=["compliance:audit:read", "service:internal"]):
    now = int(time.time())
    exp = now + 900
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": "auditor_jane",
        "preferred_username": "auditor_jane",
        "role": "COMPLIANCE_REVIEWER",
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
    sig = hmac.new(b"test_audit_jwt_secret_2026", message.encode('utf-8'), hashlib.sha256).digest()
    token = f"{message}.{_b64_encode(sig)}"
    return {"Authorization": f"Bearer {token}"}

def test_audit_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_record_and_query_audit_event():
    headers = get_auth_header()
    event_payload = {
        "document_id": "DOC-AUDIT-100",
        "service_name": "document-gateway",
        "event_type": "DOCUMENT_INGESTED",
        "payload": {"file_name": "patient_chart.pdf", "file_size": 2048}
    }
    
    response = client.post("/audit/events", json=event_payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["document_id"] == "DOC-AUDIT-100"
    assert "hmac_signature" in data
    assert "entry_hash" in data
    assert data["prev_hash"] is not None

    # Query audit trail
    query_resp = client.get("/audit/events?document_id=DOC-AUDIT-100", headers=headers)
    assert query_resp.status_code == 200
    query_data = query_resp.json()
    assert query_data["total_records"] >= 1
    assert query_data["records"][0]["document_id"] == "DOC-AUDIT-100"

def test_verify_hashchain_integrity():
    headers = get_auth_header()
    response = client.get("/audit/verify", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "intact"
    assert data["total_verified"] >= 1

@pytest.mark.anyio
async def test_audit_vault_update_and_delete_operations_rejected():
    async with AsyncSession(engine) as session:
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

        await session.rollback()

        # 2. Test DELETE rejection
        result = await session.execute(select(AuditVaultRecord).where(AuditVaultRecord.id == rec_id))
        rec_to_delete = result.scalars().first()
        with pytest.raises(AuditVaultImmutableError) as exc_info_delete:
            await session.delete(rec_to_delete)
            await session.commit()

        assert "Audit Vault records are append-only. DELETE operations are strictly forbidden" in str(exc_info_delete.value)
