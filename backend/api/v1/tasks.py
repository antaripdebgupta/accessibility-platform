"""
Task Status API routes.

Provides endpoints for checking Celery task status.
"""

from celery.result import AsyncResult
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Optional, Any

from tasks import celery_app

router = APIRouter(tags=["Tasks"])

# Response Schemas

class TaskStatusResponse(BaseModel):
    """Response schema for task status."""

    task_id: str
    status: str
    result: Optional[Any] = None
    error: Optional[str] = None
    progress: Optional[int] = None

# Routes

@router.get(
    "/{task_id}",
    response_model=TaskStatusResponse,
)
async def get_task_status(task_id: str) -> TaskStatusResponse:
    """
    Get the status of a Celery task.

    Returns the current state of the task, result if completed,
    or error details if failed.

    Args:
        task_id: The Celery task ID

    Returns:
        TaskStatusResponse with status, result, or error

    Status values:
        - PENDING: Task is waiting to be executed
        - STARTED: Task has started execution
        - SUCCESS: Task completed successfully
        - FAILURE: Task failed with an error
        - RETRY: Task is being retried
        - REVOKED: Task was cancelled
    """
    result = AsyncResult(task_id, app=celery_app)

    # Map Celery states to our API states
    celery_status = result.status

    response = TaskStatusResponse(
        task_id=task_id,
        status=celery_status,
    )

    if celery_status == "SUCCESS":
        response.result = result.result
    elif celery_status == "FAILURE":
        # Get error information safely
        try:
            error_info = str(result.info) if result.info else "Unknown error"
        except Exception:
            error_info = "Error details unavailable"
        response.error = error_info
    elif celery_status == "PROGRESS":
        # Custom progress state (if task reports progress)
        try:
            if isinstance(result.info, dict) and "progress" in result.info:
                response.progress = result.info["progress"]
        except Exception:
            pass

    return response


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def revoke_task(task_id: str) -> None:
    """
    Cancel/revoke a running or pending task.

    Attempts to terminate the task if it's currently running.

    Args:
        task_id: The Celery task ID to revoke

    Returns:
        204 No Content on success
    """
    result = AsyncResult(task_id, app=celery_app)

    # Check if task exists and is in a revocable state
    if result.status in ("SUCCESS", "FAILURE", "REVOKED"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Task cannot be revoked in state: {result.status}",
        )

    # Revoke the task (terminate=True to kill running tasks)
    result.revoke(terminate=True)
