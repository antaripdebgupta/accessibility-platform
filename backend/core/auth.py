"""FastAPI dependency for Firebase authenticated routes.

Provides a simple dependency `get_current_user` that verifies the Bearer
token using the Admin SDK (core.firebase.verify_token).
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from core.firebase import verify_token

security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Extract and verify the bearer token and return decoded claims.

    Raises HTTPException(401) on invalid or missing token.
    """
    token = credentials.credentials if credentials else None
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing or invalid authorization token")

    try:
        claims = verify_token(token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")

    return claims
