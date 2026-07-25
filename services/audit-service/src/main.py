import uuid
import json
from contextlib import asynccontextmanager
from typing import Optional, List
from fastapi import FastAPI, HTTPException, Query, status
from sqlalchemy.future import select

from src.config import settings
from src.logger import logger
from src.models import AuditEventCreate, AuditRecordResponse, AuditQueryResponse, IntegrityVerifyResponse
from src.vault_db import init_db, engine, insert_audit_event, AuditVaultRecord
from src.audit_signer import compute_entry_hash, verify_entry_hmac
from sqlalchemy.ext.asyncio import AsyncSession

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Audit Vault database tables on startup")
    await init_db()
    yield

app = FastAPI(
    title=settings.service_name,
    description="Cryptographic Append-Only Audit Vault Microservice",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": settings.service_name
    }

@app.post("/audit/events", response_model=AuditRecordResponse)
async def create_audit_event(event: AuditEventCreate):
    """Directly records a signed, append-only audit event into Audit Vault."""
    event_id = event.event_id or str(uuid.uuid4())
    async with AsyncSession(engine) as session:
        record = await insert_audit_event(
            session=session,
            event_id=event_id,
            document_id=event.document_id,
            service_name=event.service_name,
            event_type=event.event_type,
            payload=event.payload,
            timestamp=event.timestamp
        )
        
        return AuditRecordResponse(
            id=record.id,
            event_id=record.event_id,
            document_id=record.document_id,
            service_name=record.service_name,
            event_type=record.event_type,
            payload=json.loads(record.payload_json),
            prev_hash=record.prev_hash,
            entry_hash=record.entry_hash,
            hmac_signature=record.hmac_signature,
            created_at=record.created_at
        )

@app.get("/audit/events", response_model=AuditQueryResponse)
async def query_audit_trail(
    document_id: Optional[str] = Query(None, description="Filter by document ID"),
    service_name: Optional[str] = Query(None, description="Filter by service name"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    limit: int = Query(50, ge=1, le=500),
    x_user_scopes: Optional[str] = Header(None, alias="X-User-Scopes")
):
    """Exposes query API for Compliance Dashboard to retrieve signed audit logs, enforcing 'audit:read' RBAC scope."""
    if x_user_scopes is not None:
        user_scopes = [s.strip() for s in x_user_scopes.split(",")]
        if "audit:read" not in user_scopes:
            logger.warning(f"RBAC Scope Violation: Access denied for audit trail query. Required scope 'audit:read' missing.")
            raise HTTPException(status_code=403, detail="Forbidden: Missing required RBAC scope 'audit:read'")

    await init_db()
    async with AsyncSession(engine) as session:
        stmt = select(AuditVaultRecord)
        if document_id:
            stmt = stmt.where(AuditVaultRecord.document_id == document_id)
        if service_name:
            stmt = stmt.where(AuditVaultRecord.service_name == service_name)
        if event_type:
            stmt = stmt.where(AuditVaultRecord.event_type == event_type)
            
        stmt = stmt.order_by(AuditVaultRecord.id.asc()).limit(limit)
        result = await session.execute(stmt)
        records = result.scalars().all()
        
        output_list = [
            AuditRecordResponse(
                id=r.id,
                event_id=r.event_id,
                document_id=r.document_id,
                service_name=r.service_name,
                event_type=r.event_type,
                payload=json.loads(r.payload_json),
                prev_hash=r.prev_hash,
                entry_hash=r.entry_hash,
                hmac_signature=r.hmac_signature,
                created_at=r.created_at
            ) for r in records
        ]
        
        return AuditQueryResponse(
            total_records=len(output_list),
            records=output_list
        )

@app.get("/audit/verify", response_model=IntegrityVerifyResponse)
async def verify_audit_vault_integrity():
    """Cryptographically verifies hash chain and HMAC signature integrity across all Audit Vault entries."""
    await init_db()
    async with AsyncSession(engine) as session:
        stmt = select(AuditVaultRecord).order_by(AuditVaultRecord.id.asc())
        result = await session.execute(stmt)
        records = result.scalars().all()

        if not records:
            return IntegrityVerifyResponse(
                status="intact",
                total_verified=0,
                details="Audit Vault is empty."
            )

        prev_hash = "0000000000000000000000000000000000000000000000000000000000000000"
        for r in records:
            # 1. Verify prev_hash link
            if r.prev_hash != prev_hash:
                return IntegrityVerifyResponse(
                    status="compromised",
                    total_verified=r.id - 1,
                    failed_entry_id=r.id,
                    details=f"Hash chain broken at entry id={r.id}: expected prev_hash={prev_hash}, found={r.prev_hash}"
                )

            # 2. Verify recomputed entry_hash
            computed_hash = compute_entry_hash(
                r.prev_hash, r.event_id, r.document_id, r.service_name, r.event_type, r.payload_json, r.created_at
            )
            if computed_hash != r.entry_hash:
                return IntegrityVerifyResponse(
                    status="compromised",
                    total_verified=r.id - 1,
                    failed_entry_id=r.id,
                    details=f"Entry hash mismatch at entry id={r.id}"
                )

            # 3. Verify HMAC signature
            if not verify_entry_hmac(r.entry_hash, r.hmac_signature):
                return IntegrityVerifyResponse(
                    status="compromised",
                    total_verified=r.id - 1,
                    failed_entry_id=r.id,
                    details=f"HMAC signature invalid at entry id={r.id}"
                )

            prev_hash = r.entry_hash

        return IntegrityVerifyResponse(
            status="intact",
            total_verified=len(records),
            details=f"All {len(records)} Audit Vault entries verified intact."
        )
