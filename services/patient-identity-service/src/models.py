import datetime

from sqlalchemy import JSON, Date, DateTime, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass

class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    date_of_birth: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    gender: Mapped[str | None] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=lambda: datetime.datetime.now(datetime.UTC))

class QuarantineRecord(Base):
    __tablename__ = "quarantine_queue"

    document_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    first_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    date_of_birth: Mapped[str | None] = mapped_column(String(50), nullable=True)
    match_attempts: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # Logs of candidates and their matching scores
    status: Mapped[str] = mapped_column(String(20), default="pending_review")  # pending_review, resolved
    resolved_patient_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=lambda: datetime.datetime.now(datetime.UTC))
