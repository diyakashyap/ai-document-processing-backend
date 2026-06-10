from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.document import ProcessingStatus


class DocumentSummaryResponse(BaseModel):
    document_id: int
    summary_text: str
    created_at: datetime


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    doc_name: str
    doc_type: str
    doc_size_bytes: int
    status: ProcessingStatus
    error_message: str | None
    uploaded_at: datetime
    updated_at: datetime
    summary_preview: str | None = None


class UploadResponse(BaseModel):
    uploaded: list[DocumentResponse]


class DownloadUrlResponse(BaseModel):
    url: str
    expires_in_seconds: int


class UserStatsResponse(BaseModel):
    total_files: int
    completed: int
    processing: int
    failed: int
