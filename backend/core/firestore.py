"""
Firestore client wrapper for real-time data synchronization.

This module provides functions to sync evaluation data from PostgreSQL
to Firestore for real-time frontend updates. All Firestore operations
are designed to fail gracefully - they should never crash the API response.

Firestore document structure:
evaluations/{id}/
  id: string
  title: string
  target_url: string
  status: string
  wcag_version: string
  conformance_level: string
  audit_type: string
  organisation_id: string
  created_by: string
  created_at: ISO string
  updated_at: ISO string
  _source: "postgresql"
  _synced_at: ISO string
"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from core.logging import get_logger

logger = get_logger(__name__)

# Firestore client singleton
_firestore_client = None


def get_firestore_client():
    """
    Returns the Firestore client using the already-initialized Firebase Admin app.

    Returns None gracefully if Firebase is in dev-stub mode (no service account)
    or if Firestore is unavailable. Logs a warning when Firestore is unavailable.

    Returns:
        firestore.Client or None: The Firestore client, or None if unavailable.
    """
    global _firestore_client

    # Return cached client if already initialized
    if _firestore_client is not None:
        return _firestore_client

    try:
        # Import firebase_admin to check if app is initialized
        import firebase_admin
        from firebase_admin import firestore

        # Check if the default app exists
        app = firebase_admin.get_app()
        if app is None:
            logger.warning(
                "firestore_unavailable",
                reason="Firebase Admin app not initialized"
            )
            return None

        # Get the Firestore client
        _firestore_client = firestore.client()
        logger.info("firestore_client_initialized")
        return _firestore_client

    except ValueError as e:
        # No default app exists
        logger.warning(
            "firestore_unavailable",
            reason="Firebase Admin app not initialized",
            error=str(e)
        )
        return None
    except ImportError as e:
        logger.warning(
            "firestore_unavailable",
            reason="firebase-admin or google-cloud-firestore not installed",
            error=str(e)
        )
        return None
    except Exception as e:
        logger.warning(
            "firestore_unavailable",
            reason="Failed to initialize Firestore client",
            error=str(e)
        )
        return None


def _serialize_value(value: Any) -> Any:
    """
    Serialize a value for Firestore storage.

    Converts UUID fields to strings and datetime fields to ISO strings.
    Recursively handles nested dicts and lists.

    Args:
        value: The value to serialize

    Returns:
        The serialized value safe for Firestore
    """
    if value is None:
        return None
    elif isinstance(value, UUID):
        return str(value)
    elif isinstance(value, datetime):
        return value.isoformat()
    elif isinstance(value, dict):
        return {k: _serialize_value(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [_serialize_value(item) for item in value]
    else:
        return value


def _prepare_evaluation_document(evaluation: dict) -> dict:
    """
    Prepare an evaluation dict for Firestore storage.

    Converts UUID and datetime fields to strings and adds metadata fields.

    Args:
        evaluation: The evaluation data as a dictionary

    Returns:
        dict: Firestore-ready document
    """
    # Serialize all values
    doc = {k: _serialize_value(v) for k, v in evaluation.items()}

    # Add sync metadata
    doc["_source"] = "postgresql"
    doc["_synced_at"] = datetime.utcnow().isoformat()

    return doc


def sync_evaluation_to_firestore(evaluation: dict) -> None:
    """
    Sync an evaluation to Firestore.

    Writes to evaluations/{evaluation_id} collection. This function is
    async-safe and designed to be called as a fire-and-forget background task.

    A Firestore failure will NEVER crash the API response - errors are logged
    and the function returns silently.

    Args:
        evaluation: The evaluation data as a dictionary. Must contain 'id' field.
    """
    try:
        client = get_firestore_client()
        if client is None:
            logger.debug(
                "firestore_sync_skipped",
                reason="Firestore client unavailable"
            )
            return

        # Extract evaluation ID
        evaluation_id = evaluation.get("id")
        if not evaluation_id:
            logger.warning(
                "firestore_sync_failed",
                reason="Evaluation missing 'id' field"
            )
            return

        # Convert ID to string if needed
        doc_id = str(evaluation_id)

        # Prepare the document
        doc_data = _prepare_evaluation_document(evaluation)

        # Write to Firestore
        doc_ref = client.collection("evaluations").document(doc_id)
        doc_ref.set(doc_data)

        logger.info(
            "firestore_evaluation_synced",
            evaluation_id=doc_id
        )

    except Exception as e:
        # Log the error but never raise - Firestore failures must not crash the API
        logger.error(
            "firestore_sync_failed",
            evaluation_id=str(evaluation.get("id", "unknown")),
            error=str(e),
            error_type=type(e).__name__
        )


def delete_evaluation_from_firestore(evaluation_id: str) -> None:
    """
    Delete an evaluation document from Firestore.

    This function is async-safe and designed to be called as a fire-and-forget
    background task. A Firestore failure will NEVER crash the API response -
    errors are logged and the function returns silently.

    Args:
        evaluation_id: The UUID string of the evaluation to delete
    """
    try:
        client = get_firestore_client()
        if client is None:
            logger.debug(
                "firestore_delete_skipped",
                reason="Firestore client unavailable"
            )
            return

        # Delete the document
        doc_ref = client.collection("evaluations").document(evaluation_id)
        doc_ref.delete()

        logger.info(
            "firestore_evaluation_deleted",
            evaluation_id=evaluation_id
        )

    except Exception as e:
        # Log the error but never raise - Firestore failures must not crash the API
        logger.error(
            "firestore_delete_failed",
            evaluation_id=evaluation_id,
            error=str(e),
            error_type=type(e).__name__
        )
