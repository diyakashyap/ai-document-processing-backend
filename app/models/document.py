from datetime import datetime
from enum import Enum
import uuid

from sqlalchemy import DateTime, Enum as SqlEnum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ProcessingStatus(str, Enum):
    pending = "Pending"
    processing = "Processing"
    completed = "Completed"
    failed = "Failed"


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    doc_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    doc_size_bytes: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    doc_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    raw_file_s3_key: Mapped[str] = mapped_column(
        String(600),
        nullable=False
    )

    status: Mapped[ProcessingStatus] = mapped_column(
        SqlEnum(ProcessingStatus),
        default=ProcessingStatus.pending,
        nullable=False
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now()
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now()
    )

    user = relationship(
        "User",
        back_populates="documents"
    )

    summary = relationship(
        "DocumentSummary",
        back_populates="document",
        cascade="all, delete-orphan",
        uselist=False,
    )