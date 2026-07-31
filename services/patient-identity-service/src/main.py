from contextlib import asynccontextmanager
import datetime

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.config import settings
from src.database import async_session, engine, get_db
from src.logger import logger
from src.matcher import resolve_patient_identity
from src.models import Base, Patient, QuarantineRecord


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing database schemas and tables on startup")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    # Seed initial registry if empty
    async with async_session() as session:
        result = await session.execute(select(Patient))
        patients = result.scalars().all()
        if not patients:
            logger.info("Seeding initial patient records into patients registry.")
            seed_data = [
                Patient(id="PAT-001", first_name="John", last_name="Doe", date_of_birth=datetime.date(1980, 1, 1), gender="Male"),
                Patient(id="PAT-002", first_name="Jane", last_name="Smith", date_of_birth=datetime.date(1992, 5, 15), gender="Female"),
                Patient(id="PAT-003", first_name="Alice", last_name="Williams", date_of_birth=datetime.date(1975, 9, 30), gender="Female")
            ]
            session.add_all(seed_data)
            await session.commit()
    yield

app = FastAPI(
    title=settings.service_name,
    description="Patient Identity Resolution Service",
    version="0.1.0",
    lifespan=lifespan
)

class ResolutionRequest(BaseModel):
    document_id: str
    first_name: str
    last_name: str
    date_of_birth: str

class ResolveQuarantineRequest(BaseModel):
    patient_id: str

@app.post("/identity/resolve")
async def resolve_identity(req: ResolutionRequest, db: AsyncSession = Depends(get_db)):
    logger.info(
        f"Resolving patient identity for document: {req.document_id}",
        extra={"first_name": req.first_name, "last_name": req.last_name, "dob": req.date_of_birth}
    )
    
    # 1. Fetch all patient records
    result = await db.execute(select(Patient))
    patients = result.scalars().all()
    
    # 2. Run matching algorithm
    matched_patient, highest_score, candidate_logs = resolve_patient_identity(
        first_name=req.first_name,
        last_name=req.last_name,
        dob_str=req.date_of_birth,
        patients=patients
    )
    
    # 3. Handle Resolution Outcomes
    if matched_patient:
        logger.info(
            f"Successfully resolved patient for document {req.document_id}",
            extra={"document_id": req.document_id, "patient_id": matched_patient.id}
        )
        return {
            "status": "resolved",
            "patient_id": matched_patient.id,
            "confidence_score": highest_score,
            "candidates": candidate_logs
        }
        
    # 4. Handle Quarantine (Confidence below threshold)
    logger.warning(
        f"Demographics match confidence too low. Quarantining document {req.document_id}",
        extra={"document_id": req.document_id, "score": highest_score}
    )
    
    # Check if quarantine record already exists for this document
    q_result = await db.execute(select(QuarantineRecord).filter(QuarantineRecord.document_id == req.document_id))
    existing_q = q_result.scalar_one_or_none()
    
    if not existing_q:
        quarantine = QuarantineRecord(
            document_id=req.document_id,
            first_name=req.first_name,
            last_name=req.last_name,
            date_of_birth=req.date_of_birth,
            match_attempts=candidate_logs,
            status="pending_review"
        )
        db.add(quarantine)
        await db.commit()
    
    return {
        "status": "quarantined",
        "confidence_score": highest_score,
        "reason": "Probabilistic demographic matching confidence score fell below required threshold.",
        "candidates": candidate_logs
    }

@app.get("/identity/quarantine")
async def get_quarantine_queue(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(QuarantineRecord).filter(QuarantineRecord.status == "pending_review"))
    records = result.scalars().all()
    return records

@app.post("/identity/quarantine/{document_id}/resolve")
async def resolve_quarantine_item(
    document_id: str, 
    req: ResolveQuarantineRequest, 
    db: AsyncSession = Depends(get_db)
):
    # Verify patient exists
    p_result = await db.execute(select(Patient).filter(Patient.id == req.patient_id))
    patient = p_result.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=400, detail="Invalid patient_id. Target patient does not exist.")
        
    # Verify quarantine item exists
    q_result = await db.execute(select(QuarantineRecord).filter(QuarantineRecord.document_id == document_id))
    record = q_result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Quarantine record not found.")
        
    record.status = "resolved"
    record.resolved_patient_id = req.patient_id
    await db.commit()
    
    logger.info(
        f"Quarantined document {document_id} manually resolved to patient {req.patient_id}",
        extra={"document_id": document_id, "resolved_patient_id": req.patient_id}
    )
    return {"status": "success", "message": f"Document manually mapped to patient {req.patient_id}."}

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": settings.service_name}
