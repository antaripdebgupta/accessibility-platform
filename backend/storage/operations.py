"""
MinIO Storage Operations Module.

Provides functions for uploading, downloading, and managing files in MinIO.
"""

import io
from datetime import timedelta

from storage.client import get_minio_client
from core.config import settings
from core.logging import get_logger

logger = get_logger(__name__)


class StorageError(Exception):
    """Exception raised for storage operation failures."""

    def __init__(self, message: str, operation: str, bucket: str = "", key: str = ""):
        self.message = message
        self.operation = operation
        self.bucket = bucket
        self.key = key
        super().__init__(self.message)


def upload_bytes(
    bucket: str,
    key: str,
    data: bytes,
    content_type: str = "application/octet-stream",
) -> str:
    """
    Upload bytes to MinIO.

    Args:
        bucket: The bucket name
        key: The object key (path within bucket)
        data: The bytes to upload
        content_type: MIME type for the object

    Returns:
        str: The object key on success

    Raises:
        StorageError: If upload fails
    """
    try:
        client = get_minio_client()

        data_stream = io.BytesIO(data)
        data_length = len(data)

        client.put_object(
            bucket_name=bucket,
            object_name=key,
            data=data_stream,
            length=data_length,
            content_type=content_type,
        )

        logger.info(
            "minio_upload_success",
            bucket=bucket,
            key=key,
            size=data_length,
            content_type=content_type,
        )

        return key

    except Exception as e:
        logger.error(
            "minio_upload_failed",
            bucket=bucket,
            key=key,
            error=str(e),
        )
        raise StorageError(
            message=f"Failed to upload object: {str(e)}",
            operation="upload",
            bucket=bucket,
            key=key,
        ) from e


def get_presigned_url(
    bucket: str,
    key: str,
    expires_hours: int = 24,
) -> str:
    """
    Generate a presigned GET URL for an object.

    Args:
        bucket: The bucket name
        key: The object key
        expires_hours: URL expiration time in hours (default: 24)

    Returns:
        str: The presigned URL, or empty string on failure (never raises)
    """
    try:
        client = get_minio_client()

        url = client.presigned_get_object(
            bucket_name=bucket,
            object_name=key,
            expires=timedelta(hours=expires_hours),
        )

        # Replace internal Docker endpoint with external endpoint for browser access
        if settings.minio_endpoint != settings.minio_external_endpoint:
            url = url.replace(
                f"http://{settings.minio_endpoint}",
                f"http://{settings.minio_external_endpoint}",
            )
            url = url.replace(
                f"https://{settings.minio_endpoint}",
                f"https://{settings.minio_external_endpoint}",
            )

        logger.debug(
            "minio_presigned_url_generated",
            bucket=bucket,
            key=key,
            expires_hours=expires_hours,
        )

        return url

    except Exception as e:
        logger.error(
            "minio_presigned_url_failed",
            bucket=bucket,
            key=key,
            error=str(e),
        )
        return ""


def delete_object(bucket: str, key: str) -> None:
    """
    Delete an object from MinIO.

    Silently ignores errors - logs them but never raises.

    Args:
        bucket: The bucket name
        key: The object key to delete
    """
    try:
        client = get_minio_client()

        client.remove_object(
            bucket_name=bucket,
            object_name=key,
        )

        logger.info(
            "minio_delete_success",
            bucket=bucket,
            key=key,
        )

    except Exception as e:
        logger.error(
            "minio_delete_failed",
            bucket=bucket,
            key=key,
            error=str(e),
        )
