from io import BytesIO
from uuid import uuid4

import boto3
from fastapi import HTTPException, status

from app.core.config import settings


def get_s3_client():
    return boto3.client(
        "s3",
        region_name=settings.aws_region,
        aws_access_key_id=settings.aws_access_key_id or None,
        aws_secret_access_key=settings.aws_secret_access_key or None,
    )


def ensure_bucket_configured() -> None:
    if not settings.aws_s3_bucket_name:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="S3 bucket is not configured. Set AWS_S3_BUCKET_NAME in .env.",
        )


def build_s3_key(user_id: int, file_name: str) -> str:
    safe_name = file_name.replace("/", "_").replace("\\", "_")
    return f"users/{user_id}/documents/{uuid4()}-{safe_name}"


def upload_original_file(content: bytes, key: str, content_type: str) -> None:
    ensure_bucket_configured()
    get_s3_client().upload_fileobj(
        BytesIO(content),
        settings.aws_s3_bucket_name,
        key,
        ExtraArgs={"ContentType": content_type},
    )


def download_original_file(key: str) -> bytes:
    ensure_bucket_configured()
    buffer = BytesIO()
    get_s3_client().download_fileobj(settings.aws_s3_bucket_name, key, buffer)
    return buffer.getvalue()


def create_presigned_download_url(key: str) -> str:
    ensure_bucket_configured()
    return get_s3_client().generate_presigned_url(
        ClientMethod="get_object",
        Params={"Bucket": settings.aws_s3_bucket_name, "Key": key},
        ExpiresIn=settings.s3_presigned_url_expire_seconds,
    )
