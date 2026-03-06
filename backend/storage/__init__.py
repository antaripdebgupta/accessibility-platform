"""
MinIO Storage Package.

Provides client and operations for file storage with MinIO.
"""

from storage.client import get_minio_client, ensure_buckets
from storage.operations import upload_bytes, get_presigned_url, delete_object, StorageError

__all__ = [
    "get_minio_client",
    "ensure_buckets",
    "upload_bytes",
    "get_presigned_url",
    "delete_object",
    "StorageError",
]
