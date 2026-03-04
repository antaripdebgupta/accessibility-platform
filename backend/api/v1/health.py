from fastapi import APIRouter
from datetime import datetime, timezone

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    """
    Health check endpoint.
    Used by Docker healthchecks and load balancers.
    Returns 200 when the API process is running.
    """
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "accessibility-platform-api",
    }
