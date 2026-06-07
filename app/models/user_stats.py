from datetime import datetime
import uuid

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class UserStats(Base):
    __tablename__ = "user_stats"

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id"),
        primary_key=True
    )

    total_documents: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )

    total_processed: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )

    total_failed: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )

    total_storage_mb: Mapped[float] = mapped_column(
        Float,
        default=0,
        nullable=False
    )

    last_upload_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now()
    )

    user = relationship(
        "User",
        back_populates="stats"
    )