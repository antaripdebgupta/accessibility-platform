"""
Firebase Admin SDK initialization and token verification.

This module initializes the Admin SDK in two modes:
 - development (emulator): when ENV=development or settings.debug==True.
   It will set the required emulator environment variables and initialize
   an app (with or without a service account key).
 - production: loads credentials from a service account file pointed to by
   the environment / settings and initializes the real Admin SDK.

The module exposes:
 - init_firebase(): call once at startup
 - verify_token(id_token): verifies Firebase ID tokens (works with emulator)

Security note: do NOT enable the dev bypass in production. Service account
paths and production secrets must be provided via environment variables and
secrets (not committed to git).
"""

import os
from typing import Optional

import firebase_admin
from firebase_admin import auth as firebase_auth
from firebase_admin import credentials

from core.config import settings
from core.logging import get_logger

logger = get_logger(__name__)

# Global Firebase App handle
_firebase_app: Optional[firebase_admin.App] = None

# Dev bypass token (only when running with debug and explicitly desired).
# NEVER rely on this in production.
DEV_BYPASS_TOKEN = "dev-bypass-token-local-only"
DEV_BYPASS_UID = "dev-uid-000"
DEV_BYPASS_EMAIL = "dev@local.test"

# Emulator defaults (kept in sync with firebase.json)
EMULATOR_HOST = "127.0.0.1"
AUTH_EMULATOR_PORT = 9099
FIRESTORE_EMULATOR_PORT = 8080


def init_firebase() -> None:
    """Initialise Firebase Admin SDK.

    Behavior:
      - If running in development (ENV=development or settings.debug), set the
        emulator environment variables and initialize an app. If a service
        account key exists use it; otherwise initialize with the project ID so
        emulator calls succeed.
      - In production, attempt to initialize using the service account key
        referenced in settings.firebase_service_account_key.
    """
    global _firebase_app

    env_mode = os.getenv("ENV", "").lower()
    dev_mode = env_mode == "development" or bool(settings.debug)

    # If running in dev-mode, configure emulator host env vars so Admin SDK
    # and downstream clients use the emulator endpoints.
    if dev_mode:
        os.environ.setdefault("FIREBASE_AUTH_EMULATOR_HOST", f"{EMULATOR_HOST}:{AUTH_EMULATOR_PORT}")
        # Firestore emulator variable expected by google-cloud-firestore
        os.environ.setdefault("FIRESTORE_EMULATOR_HOST", f"{EMULATOR_HOST}:{FIRESTORE_EMULATOR_PORT}")
        # Project id helps the Admin SDK and emulators route calls
        if settings.firebase_project_id:
            os.environ.setdefault("GOOGLE_CLOUD_PROJECT", settings.firebase_project_id)

        logger.info("firebase_emulator_mode", auth=os.environ.get("FIREBASE_AUTH_EMULATOR_HOST"), firestore=os.environ.get("FIRESTORE_EMULATOR_HOST"))

    key_path = settings.firebase_service_account_key

    # Try to initialize the admin SDK with available credentials. In dev-mode
    # it's acceptable to initialize without a service account so emulator calls
    # still work.
    try:
        if key_path and os.path.exists(key_path):
            cred = credentials.Certificate(key_path)
            _firebase_app = firebase_admin.initialize_app(cred, {"projectId": settings.firebase_project_id} if settings.firebase_project_id else None)
            logger.info("firebase_initialised_with_key", key_path=key_path)
        else:
            # No key file available. Initialize without credentials if possible
            # (emulator or ADC). This is safe for local dev/emulator testing.
            _firebase_app = firebase_admin.initialize_app(options={"projectId": settings.firebase_project_id} if settings.firebase_project_id else None)
            logger.warning("firebase_initialised_without_key", path=key_path, message="Running without a service account file; ensure this is only for development/emulator usage.")
    except Exception as exc:  # pragma: no cover - log and surface the error
        logger.exception("firebase_initialization_failed", error=str(exc))
        _firebase_app = None


def verify_token(id_token: str) -> dict:
    """Verify a Firebase ID token and return decoded claims.

    Returns a dict with at minimum: {"uid": str, "email": str}
    Raises firebase_admin.auth.InvalidIdTokenError or ValueError on failure.
    """
    # Dev bypass — convenient for local development when explicit testing is needed
    if (bool(settings.debug) or os.getenv("ENV", "").lower() == "development") and id_token == DEV_BYPASS_TOKEN:
        logger.debug("firebase_dev_bypass_used")
        return {"uid": DEV_BYPASS_UID, "email": DEV_BYPASS_EMAIL, "name": "Dev User"}

    if _firebase_app is None:
        raise ValueError("Firebase is not initialised. Call init_firebase() and ensure credentials or emulators are available.")

    decoded = firebase_auth.verify_id_token(id_token, app=_firebase_app)
    return decoded
