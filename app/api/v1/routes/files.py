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


@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_file(
    doc_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    document = get_owned_document(db, doc_id, current_user)
    db.delete(document)
    db.commit()
    return None


@router.get("/{doc_id}/download", response_model=DownloadUrlResponse)
def get_file_download_url(
    doc_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    document = get_owned_document(db, doc_id, current_user)

    return DownloadUrlResponse(
        url=create_presigned_download_url(document.raw_file_s3_key),
        expires_in_seconds=settings.s3_presigned_url_expire_seconds,
    )


@router.get("/{doc_id}/summary", response_model=DocumentSummaryResponse)
def get_document_summary(
    doc_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    document = get_owned_document(db, doc_id, current_user)

    if not document.summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Summary not available.",
        )

    return DocumentSummaryResponse(
        document_id=document.id,
        summary_text=document.summary.summary_text,
        created_at=document.summary.created_at,
    )


@router.get("/{doc_id}/summary/download")
def download_summary_txt(
    doc_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    document = get_owned_document(db, doc_id, current_user)

    if not document.summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Summary not available.",
        )

    file_name = f"{document.doc_name}-summary.txt"

    return StreamingResponse(
        BytesIO(document.summary.summary_text.encode("utf-8")),
        media_type="text/plain",
        headers={
            "Content-Disposition": f'attachment; filename="{file_name}"'
        },
    )


@router.post("/{doc_id}/retry", response_model=DocumentResponse)
def retry_processing(
    doc_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    document = get_owned_document(db, doc_id, current_user)

    document.status = ProcessingStatus.processing
    document.error_message = None

    db.commit()

    try:
        content = download_original_file(document.raw_file_s3_key)
        process_document_content(db, document, content)

    except Exception as exc:
        document.status = ProcessingStatus.failed
        document.error_message = str(exc)

    db.commit()
    db.refresh(document)

    return to_document_response(document)


@router.get("/{doc_id}", response_model=DocumentResponse)
def get_file_details(
    doc_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return to_document_response(
        get_owned_document(db, doc_id, current_user)
    )