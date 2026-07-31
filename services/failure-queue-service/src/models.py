from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class FailureQueueRecord(Base):
    __tablename__ = "failure_queue"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_id: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    service_name: Mapped[str] = mapped_column(String(64), nullable=False)
    error_type: Mapped[str] = mapped_column(String(128), nullable=False)
    error_message: Mapped[str] = mapped_column(Text, nullable=False)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="queued")
    enqueued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    next_retry_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    redriven_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    redriven_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class FailureEnqueueRequest(BaseModel):
    document_id: str
    service_name: str
    error_type: str = Field(..., description="'LOW_CONFIDENCE_EXTRACTION', 'SERVICE_EXCEPTION', 'CLINICIAN_REJECTION'")
    error_message: str
    payload: dict[str, Any] = Field(default_factory=dict)


class FailureItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    document_id: str
    service_name: str
    error_type: str
    error_message: str
    retry_count: int
    max_retries: int
    status: str = Field(..., description="'queued', 'retrying', 'manual_review'")
    enqueued_at: datetime | str


class DLQSummaryResponse(BaseModel):
    total_items: int
    manual_review_items: int
    items: list[FailureItemResponse]
