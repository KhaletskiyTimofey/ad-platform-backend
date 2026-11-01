import io
import uuid

from minio import Minio

from app.config import settings

client = Minio(
    settings.MINIO_ENDPOINT,
    access_key=settings.MINIO_ACCESS_KEY,
    secret_key=settings.MINIO_SECRET_KEY,
    secure=False,
)


def ensure_bucket() -> None:
    if not client.bucket_exists(settings.MINIO_BUCKET):
        client.make_bucket(settings.MINIO_BUCKET)
    # Публичный read-only доступ к объектам (для хакатона — ок)
    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"AWS": ["*"]},
                "Action": ["s3:GetObject"],
                "Resource": [f"arn:aws:s3:::{settings.MINIO_BUCKET}/*"],
            }
        ],
    }
    import json

    try:
        client.set_bucket_policy(settings.MINIO_BUCKET, json.dumps(policy))
    except Exception:  # noqa: BLE001
        pass


def upload_file(file_data: bytes, filename: str, content_type: str) -> str:
    object_name = f"{uuid.uuid4()}_{filename}"
    client.put_object(
        settings.MINIO_BUCKET,
        object_name,
        io.BytesIO(file_data),
        length=len(file_data),
        content_type=content_type or "application/octet-stream",
    )
    return f"{settings.MINIO_PUBLIC_URL}/{settings.MINIO_BUCKET}/{object_name}"