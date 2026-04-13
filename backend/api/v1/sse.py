"""
Server-Sent Events (SSE) API Routes.

Provides real-time streaming of Celery task progress events to browser clients.
Uses Redis pub/sub as the event bus between Celery workers and FastAPI.

SSE replaces polling with a persistent HTTP connection that streams events
as they happen, providing:
- Instant UI updates (no 3-second polling delay)
- Reduced server load (no unnecessary requests)
- Granular progress (per-page crawl/scan updates)
"""

import json
from typing import AsyncGenerator

from celery.result import AsyncResult
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth import get_current_user_sse
from core.events import subscribe_task_events, make_event
from core.logging import get_logger
from db.session import get_db
from tasks import celery_app

logger = get_logger(__name__)

router = APIRouter(tags=["SSE"])


def format_sse(data: dict) -> str:
    """
    Format a dict as an SSE message.

    SSE format requires:
    - Each event is prefixed with "data: "
    - Events are separated by double newlines

    Args:
        data: Dict to serialize as JSON

    Returns:
        Formatted SSE message string
    """
    json_data = json.dumps(data)
    return f"data: {json_data}\n\n"


async def event_generator(task_id: str) -> AsyncGenerator[str, None]:
    """
    Async generator that yields SSE-formatted events for a task.

    Flow:
    1. Check if task is already completed (instant response)
    2. Yield "connected" event
    3. Subscribe to Redis and stream events
    4. Yield "stream_end" when done

    Args:
        task_id: The Celery task ID to stream events for

    Yields:
        SSE-formatted event strings
    """
    logger.info(
        "sse_stream_starting",
        task_id=task_id,
    )

    try:
        # Step 1: Check if task already completed
        result = AsyncResult(task_id, app=celery_app)
        celery_status = result.status

        if celery_status == "SUCCESS":
            # Task already done - yield complete event immediately
            logger.info(
                "sse_task_already_complete",
                task_id=task_id,
            )
            yield format_sse(make_event("complete", {
                "step": "complete",
                "message": "Task completed",
                "result": result.result if isinstance(result.result, dict) else {},
            }))
            yield format_sse({"type": "stream_end"})
            return

        if celery_status == "FAILURE":
            # Task already failed - yield error event immediately
            try:
                error_info = str(result.info) if result.info else "Unknown error"
            except Exception:
                error_info = "Error details unavailable"

            logger.info(
                "sse_task_already_failed",
                task_id=task_id,
                error=error_info,
            )
            yield format_sse(make_event("error", {
                "step": "error",
                "message": error_info,
            }))
            yield format_sse({"type": "stream_end"})
            return

        # Step 2: Yield initial connected event
        yield format_sse({"type": "connected", "task_id": task_id})

        # Step 3: Subscribe to Redis and stream events
        async for event in subscribe_task_events(task_id):
            yield format_sse(event)

            # Check for terminal events
            event_type = event.get("type")
            if event_type in ("complete", "error"):
                break

        # Step 4: Yield final stream_end event
        yield format_sse({"type": "stream_end"})

    except Exception as e:
        logger.error(
            "sse_stream_error",
            task_id=task_id,
            error=str(e),
        )
        yield format_sse(make_event("error", {
            "step": "error",
            "message": f"Stream error: {str(e)}",
        }))
        yield format_sse({"type": "stream_end"})

    finally:
        logger.info(
            "sse_stream_ended",
            task_id=task_id,
        )


@router.get(
    "/{task_id}/stream",
    response_class=StreamingResponse,
    summary="Stream task events via SSE",
    description="""
    Stream real-time progress events for a Celery task using Server-Sent Events.

    ## Authentication

    Provide Firebase token via either:
    - `Authorization: Bearer <token>` header
    - `?token=<token>` query parameter (required for EventSource)

    ## Event Types

    - `connected`: Connection established successfully
    - `progress`: Task progress update (step, message, percent, etc.)
    - `complete`: Task finished successfully
    - `error`: Task failed or stream error
    - `heartbeat`: Keep-alive ping (every 30 seconds)
    - `stream_end`: Stream is closing

    ## Event Data

    Progress events include contextual data depending on task type:

    **Crawl tasks:**
    - `step`: "started" | "exploring" | "page_found" | "complete"
    - `pages_found`: Number of pages discovered
    - `page_url`: URL of discovered page
    - `page_type`: Type classification of page

    **Scan tasks:**
    - `step`: "started" | "scanning_page" | "page_complete" | "complete"
    - `pages_scanned`: Number of pages scanned
    - `pages_total`: Total pages to scan
    - `percent`: Progress percentage (0-100)
    - `findings_found`: Issues found on current page

    **Report tasks:**
    - `step`: "started" | "verdict_computed" | "full_generated" | "earl_generated" | "csv_generated" | "complete"
    - `verdict`: Conformance verdict
    - `report_type`: Type of report generated

    ## Connection Limits

    - Heartbeats sent every 30 seconds
    - Connection timeout: 30 minutes
    - Automatic cleanup on disconnect

    ## Example Usage (JavaScript)

    ```javascript
    const token = await auth.currentUser.getIdToken();
    const url = `/api/v1/tasks/${taskId}/stream?token=${token}`;
    const eventSource = new EventSource(url);

    eventSource.onmessage = (e) => {
      const event = JSON.parse(e.data);
      console.log(event.type, event.data);
    };
    ```
    """,
)
async def stream_task_events(
    task_id: str,
    token: str | None = Query(None, description="Firebase auth token (alternative to Authorization header)"),
    user=Depends(get_current_user_sse),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """
    Stream real-time task events via Server-Sent Events.

    Returns a StreamingResponse with text/event-stream content type.
    Events are pushed from Celery workers through Redis pub/sub.

    Args:
        task_id: The Celery task ID to stream
        token: Optional Firebase token (for EventSource which can't set headers)
        user: Authenticated user (from header or query param token)
        db: Database session

    Returns:
        StreamingResponse with SSE event stream
    """
    logger.info(
        "sse_endpoint_called",
        task_id=task_id,
        user_id=str(user.id) if user else None,
    )

    return StreamingResponse(
        event_generator(task_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Disable Nginx buffering
            "Connection": "keep-alive",
        },
    )
