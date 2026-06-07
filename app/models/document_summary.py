from datetime import datetime
import uuid

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class DocumentSummary(Base):
    __tablename__ = "document_summary"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    doc_id: Mapped[str] = mapped_column(
        ForeignKey("documents.id"),
        unique=True,
        nullable=False,
        index=True
    )

    summary_text: Mapped[str] = mapped_column(
        LONGTEXT,
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now()
    )

    document = relationship(
        "Document",
        back_populates="summary"
    )