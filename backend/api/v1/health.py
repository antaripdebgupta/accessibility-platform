from fastapi import APIRouter, HTTPException
from datetime import datetime, timezone
import subprocess

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


@router.post("/setup/seed-wcag")
async def seed_wcag_data():
    """
    Seed WCAG criteria data.

    Call this endpoint once after initial deployment to populate
    the WCAG success criteria table. Safe to call multiple times
    (uses upsert logic).

    This endpoint exists because Render free tier doesn't have shell access.
    """
    try:
        result = subprocess.run(
            ["python", "-m", "scripts.seed_wcag"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode == 0:
            return {
                "status": "success",
                "message": "WCAG criteria seeded successfully",
                "output": result.stdout.strip(),
            }
        else:
            raise HTTPException(
                status_code=500,
                detail={
                    "status": "error",
                    "message": "Seeding failed",
                    "error": result.stderr.strip(),
                },
            )
    except subprocess.TimeoutExpired:
        raise HTTPException(
            status_code=504,
            detail={"status": "error", "message": "Seeding timed out after 120s"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"status": "error", "message": str(e)},
        )
