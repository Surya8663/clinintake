import datetime

from sqlalchemy import JSON, Column, Date, DateTime, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Patient(Base):
    __tablename__ = "patients"
    
    id = Column(String(50), primary_key=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    date_of_birth = Column(Date, nullable=False)
    gender = Column(String(20), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.UTC))

class QuarantineRecord(Base):
    __tablename__ = "quarantine_queue"
    
    document_id = Column(String(50), primary_key=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    date_of_birth = Column(String(50), nullable=True)
    match_attempts = Column(JSON, nullable=True)  # Logs of candidates and their matching scores
    status = Column(String(20), default="pending_review")  # pending_review, resolved
    resolved_patient_id = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.UTC))
