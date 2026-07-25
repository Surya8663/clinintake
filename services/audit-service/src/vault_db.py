import json
import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import Column, Integer, String, Text, DateTime, event
from sqlalchemy.orm import declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.future import select

from src.config import settings
from src.audit_signer import compute_entry_hash, compute_hmac_signature, verify_entry_hmac
from src.logger import logger

Base = declarative_base()

class AuditVaultImmutableError(Exception):
    """Raised when an UPDATE or DELETE operation is attempted on Audit Vault."""
    pass

class AuditVaultRecord(Base):
    __tablename__ = "audit_vault"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(64), nullable=False)
    document_id = Column(String(64), nullable=False, index=True)
    service_name = Column(String(64), nullable=False, index=True)
    event_type = Column(String(64), nullable=False, index=True)
    payload_json = Column(Text, nullable=False)
    prev_hash = Column(String(64), nullable=False)
    entry_hash = Column(String(64), nullable=False, unique=True)
    hmac_signature = Column(String(64), nullable=False)
    created_at = Column(String(64), nullable=False)

# ENFORCE STRICT APPEND-ONLY IMMUTABILITY AT ORM / DB LAYER
@event.listens_for(AuditVaultRecord, "before_update")
def block_audit_vault_update(mapper, connection, target):
    logger.error("Security Violation: Attempted UPDATE on Audit Vault entry!")
    raise AuditVaultImmutableError("Audit Vault records are append-only. UPDATE operations are strictly forbidden.")

@event.listens_for(AuditVaultRecord, "before_delete")
def block_audit_vault_delete(mapper, connection, target):
    logger.error("Security Violation: Attempted DELETE on Audit Vault entry!")
    raise AuditVaultImmutableError("Audit Vault records are append-only. DELETE operations are strictly forbidden.")

engine = create_async_engine(settings.vault_database_url, echo=False)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def insert_audit_event(session: AsyncSession, event_id: str, document_id: str, service_name: str, event_type: str, payload: Dict[str, Any], timestamp: Optional[str] = None) -> AuditVaultRecord:
    """Computes hash-chaining and HMAC signature, then appends to Audit Vault."""
    await init_db()
    # Get last entry hash
    result = await session.execute(select(AuditVaultRecord).order_by(AuditVaultRecord.id.desc()).limit(1))
    last_record = result.scalars().first()
    
    prev_hash = last_record.entry_hash if last_record else "0000000000000000000000000000000000000000000000000000000000000000"
    created_at = timestamp or datetime.datetime.utcnow().isoformat()
    payload_json = json.dumps(payload, sort_keys=True)
    
    entry_hash = compute_entry_hash(prev_hash, event_id, document_id, service_name, event_type, payload_json, created_at)
    signature = compute_hmac_signature(entry_hash)

    record = AuditVaultRecord(
        event_id=event_id,
        document_id=document_id,
        service_name=service_name,
        event_type=event_type,
        payload_json=payload_json,
        prev_hash=prev_hash,
        entry_hash=entry_hash,
        hmac_signature=signature,
        created_at=created_at
    )
    
    session.add(record)
    await session.commit()
    await session.refresh(record)
    
    logger.info(f"Appended signed audit event id={record.id} event_type={event_type} doc_id={document_id}")
    return record
