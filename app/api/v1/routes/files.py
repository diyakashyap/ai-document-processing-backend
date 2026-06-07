from io import BytesIO
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.db.session import get_db
from app.models.document import Document, ProcessingStatus
from app.models.document_summary import DocumentSummary
from app.models.user import User
from app.schemas.document import (
    DocumentResponse,
    DocumentSummaryResponse,
    DownloadUrlResponse,
    UploadResponse,
)
from app.services.bedrock_service import summarize_text
from app.services.file_validation import validate_file, validate_upload_count
from app.services.s3_service import (
    build_s3_key,
    create_presigned_download_url,
    download_original_file,
    upload_original_file,
)
from app.services.text_extraction import extract_text

router = APIRouter()


def to_document_response(document: Document) -> DocumentResponse:
    summary_preview = None
    if document.summary and document.summary.summary_text:
        summary_preview = document.summary.summary_text[:180]
    return DocumentResponse.model_validate(document).model_copy(
        update={"summary_preview": summary_preview}
    )


def get_owned_document(db: Session, doc_id: int, user: User) -> Document:
    document = (
        db.query(Document)
        .filter(Document.id == doc_id, Document.user_id == user.id)
        .first()
    )
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")
    return document


def process_document_content(db: Session, document: Document, content: bytes) -> None:
    extracted_text = extract_text(document.file_name, content)
    summary_text = summarize_text(extracted_text)

    if document.summary:
        document.summary.extracted_text = extracted_text
        document.summary.summary_text = summary_text
    else:
        db.add(
            DocumentSummary(
                document_id=document.id,
                extracted_text=extracted_text,
                summary_text=summary_text,
            )
        )

    document.status = ProcessingStatus.completed
    document.error_message = None


@router.post("/upload", response_model=UploadResponse)
async def upload_files(
    files: Annotated[list[UploadFile], File()],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    validate_upload_count(files)
    uploaded_documents: list[Document] = []

    for file in files:
        content = await file.read()
        validate_file(file, content)

        s3_key = build_s3_key(current_user.id, file.filename or "document")
        document = Document(
            user_id=current_user.id,
            doc_name=file.filename or "document",
            doc_type=file.content_type or "application/octet-stream",
            doc_size_bytes=len(content),
            raw_file_s3_key=s3_key,
            status=ProcessingStatus.pending,
        )
        db.add(document)
        db.commit()
        db.refresh(document)

        try:
            document.status = ProcessingStatus.processing
            db.commit()

            upload_original_file(content, s3_key, document.content_type)
            process_document_content(db, document, content)
        except Exception as exc:
            document.status = ProcessingStatus.failed
            document.error_message = str(exc)

        db.commit()
        db.refresh(document)
        uploaded_documents.append(document)

    return UploadResponse(uploaded=[to_document_response(doc) for doc in uploaded_documents])


@router.get("", response_model=list[DocumentResponse])
def list_files(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    documents = (
        db.query(Document)
        .filter(Document.user_id == current_user.id)
        .order_by(Document.uploaded_at.desc())
        .all()
    )
    return [to_document_response(document) for document in documents]


@router.get("/{doc_id}", response_model=DocumentResponse)
def get_file_details(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return to_document_response(get_owned_document(db, doc_id, current_user))


@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_file(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    document = get_owned_document(db, doc_id, current_user)
    db.delete(document)
    db.commit()
    return None


@router.get("/{doc_id}/download", response_model=DownloadUrlResponse)
def get_file_download_url(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    document = get_owned_document(db, doc_id, current_user)
    return DownloadUrlResponse(
        url=create_presigned_download_url(document.s3_key),
        expires_in_seconds=settings.s3_presigned_url_expire_seconds,
    )


@router.get("/{doc_id}/summary", response_model=DocumentSummaryResponse)
def get_document_summary(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    document = get_owned_document(db, doc_id, current_user)
    if not document.summary:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Summary not available.")
    return DocumentSummaryResponse(
        document_id=document.id,
        summary_text=document.summary.summary_text,
        created_at=document.summary.created_at,
    )


@router.get("/{doc_id}/summary/download")
def download_summary_txt(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    document = get_owned_document(db, doc_id, current_user)
    if not document.summary:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Summary not available.")

    file_name = f"{document.file_name}-summary.txt"
    return StreamingResponse(
        BytesIO(document.summary.summary_text.encode("utf-8")),
        media_type="text/plain",
        headers={"Content-Disposition": f'attachment; filename="{file_name}"'},
    )


@router.post("/{doc_id}/retry", response_model=DocumentResponse)
def retry_processing(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    document = get_owned_document(db, doc_id, current_user)
    if document.status != ProcessingStatus.failed or document.retry_count >= 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Retry is available only once for failed documents.",
        )

    document.retry_count += 1
    document.status = ProcessingStatus.processing
    document.error_message = None
    db.commit()

    try:
        content = download_original_file(document.s3_key)
        process_document_content(db, document, content)
    except Exception as exc:
        document.status = ProcessingStatus.failed
        document.error_message = str(exc)

    db.commit()
    db.refresh(document)
    return to_document_response(document)
