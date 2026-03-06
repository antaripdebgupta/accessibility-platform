"""
MinIO Client Module.

Provides a singleton MinIO client and bucket initialization.
"""

from typing import Optional

from minio import Minio

from core.config import settings
from core.logging import get_logger

logger = get_logger(__name__)

# Singleton client instance
_minio_client: Optional[Minio] = None


def get_minio_client() -> Minio:
    """
    Get the singleton MinIO client instance.

    Creates the client on first call using settings from config.

    Returns:
        Minio: The MinIO client instance
    """
    global _minio_client

    if _minio_client is None:
        _minio_client = Minio(
            endpoint=settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
        )
        logger.info(
            "minio_client_created",
            endpoint=settings.minio_endpoint,
            secure=settings.minio_secure,
        )

    return _minio_client


def ensure_buckets() -> None:
    """
    Ensure required buckets exist in MinIO.

    Creates 'screenshots' and 'reports' buckets if they don't exist.
    This should be called once on worker startup.

    Never raises exceptions - logs errors and continues.
    """
    try:
        client = get_minio_client()

        buckets_to_create = [
            settings.minio_bucket_screenshots,
            settings.minio_bucket_reports,
        ]

        for bucket_name in buckets_to_create:
            try:
                if not client.bucket_exists(bucket_name):
                    client.make_bucket(bucket_name)
                    logger.info(
                        "minio_bucket_created",
                        bucket=bucket_name,
                    )
                else:
                    logger.debug(
                        "minio_bucket_exists",
                        bucket=bucket_name,
                    )
            except Exception as bucket_error:
                logger.error(
                    "minio_bucket_creation_failed",
                    bucket=bucket_name,
                    error=str(bucket_error),
                )

        logger.info("minio_buckets_verified")

    except Exception as e:
        logger.error(
            "minio_ensure_buckets_failed",
            error=str(e),
        )
