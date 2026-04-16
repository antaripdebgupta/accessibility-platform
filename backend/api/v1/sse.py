"""
SSE (Server-Sent Events) endpoint for real-time task progress streaming.

Key design decisions:
  - 25s heartbeat (SSE comment) keeps Render's 60s proxy from killing idle streams
  - Polls Celery state for up to 10s when task hasn't been picked up yet,
    so the client doesn't get an empty stream and immediately reconnect-loop
  - Returns Last-Event-ID header so browsers resume from the right point
  - stream_end sentinel lets the client close the EventSource cleanly
"""

import asyncio
import json
import time
from typing import AsyncGenerator

from celery.result import AsyncResult
from fastapi import APIRouter, Depends, Header, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth import get_current_user_sse
from core.events import subscribe_task_events, make_event
from core.logging import get_logger
from db.session import get_db
from tasks import celery_app

logger = get_logger(__name__)
router = APIRouter(tags=["SSE"])

HEARTBEAT_INTERVAL = 20      # seconds — safely under Render's 60s proxy timeout
TASK_PENDING_WAIT   = 15     # max seconds to wait for a PENDING task to start
TASK_POLL_INTERVAL  = 1.0    # how often to check Celery state while pending


def _sse_data(payload: dict, event_id: int | None = None) -> str:
    """Format a data frame, optionally with an id: line for reconnect support."""
    lines = []
    if event_id is not None:
        lines.append(f"id: {event_id}")
    lines.append(f"data: {json.dumps(payload)}")
    lines.append("")          # blank line terminates the frame
    lines.append("")
    return "\n".join(lines)


def _sse_heartbeat() -> str:
    """SSE comment — browsers/proxies ignore it; TCP stays alive."""
    return ": heartbeat\n\n"


async def _wait_for_task_start(task_id: str) -> str:
    """
    Poll Celery until the task leaves PENDING state or we time out.
    Returns the final Celery status string.
    """
    deadline = time.monotonic() + TASK_PENDING_WAIT
    while time.monotonic() < deadline:
        status = str(AsyncResult(task_id, app=celery_app).status)
        if status != "PENDING":
            return status
        await asyncio.sleep(TASK_POLL_INTERVAL)
    return "PENDING"


async def event_generator(
    task_id: str,
    last_event_id: int | None,
) -> AsyncGenerator[str, None]:
    logger.info("sse_stream_starting", task_id=task_id)
    event_seq = (last_event_id or 0) + 1   # monotonic counter for id: lines

    try:
        result     = AsyncResult(task_id, app=celery_app)
        celery_status = result.status

        if celery_status == "SUCCESS":
            logger.info("sse_task_already_complete", task_id=task_id)
            yield _sse_data(make_event("complete", {
                "step": "complete",
                "message": "Task completed",
                "result": result.result if isinstance(result.result, dict) else {},
            }), event_seq)
            yield _sse_data({"type": "stream_end"})
            return

        if celery_status == "FAILURE":
            error_info = "Unknown error"
            try:
                error_info = str(result.info) if result.info else "Unknown error"
            except Exception:
                pass
            logger.info("sse_task_already_failed", task_id=task_id, error=error_info)
            yield _sse_data(make_event("error", {"step": "error", "message": error_info}), event_seq)
            yield _sse_data({"type": "stream_end"})
            return

        yield _sse_data({"type": "connected", "task_id": task_id}, event_seq)
        event_seq += 1

        if celery_status == "PENDING":
            logger.info("sse_waiting_for_task_start", task_id=task_id)
            # Send a heartbeat immediately so the proxy doesn't drop us
            yield _sse_heartbeat()

            celery_status = await _wait_for_task_start(task_id)

            if celery_status == "PENDING":
                # Task never started — worker may be down
                logger.warning("sse_task_still_pending_timeout", task_id=task_id)
                yield _sse_data(make_event("progress", {
                    "step": "queued",
                    "message": "Task is queued — waiting for a worker...",
                }), event_seq)
                event_seq += 1
                # Fall through to the streaming loop; it'll pick up events
                # whenever the worker actually starts.

            elif celery_status in ("SUCCESS", "FAILURE"):
                # Raced — finished while we were polling
                result = AsyncResult(task_id, app=celery_app)
                if celery_status == "SUCCESS":
                    yield _sse_data(make_event("complete", {
                        "step": "complete",
                        "message": "Task completed",
                        "result": result.result if isinstance(result.result, dict) else {},
                    }), event_seq)
                else:
                    yield _sse_data(make_event("error", {
                        "step": "error",
                        "message": str(result.info or "Task failed"),
                    }), event_seq)
                yield _sse_data({"type": "stream_end"})
                return

        async for event in _stream_with_heartbeat(task_id):
            if event is None:
                # Heartbeat slot
                yield _sse_heartbeat()
                continue

            yield _sse_data(event, event_seq)
            event_seq += 1

            if event.get("type") in ("complete", "error"):
                break

        yield _sse_data({"type": "stream_end"})

    except asyncio.CancelledError:
        logger.info("sse_client_disconnected", task_id=task_id)

    except Exception as e:
        logger.error("sse_stream_error", task_id=task_id, error=str(e))
        yield _sse_data(make_event("error", {
            "step": "error",
            "message": f"Stream error: {str(e)}",
        }))
        yield _sse_data({"type": "stream_end"})

    finally:
        logger.info("sse_stream_ended", task_id=task_id)


async def _stream_with_heartbeat(task_id: str):
    """
    Wraps subscribe_task_events() and yields None (heartbeat signal) when no
    real event arrives within HEARTBEAT_INTERVAL seconds.
    """
    event_iter = subscribe_task_events(task_id).__aiter__()

    while True:
        try:
            event = await asyncio.wait_for(
                event_iter.__anext__(),
                timeout=HEARTBEAT_INTERVAL,
            )
            yield event

        except asyncio.TimeoutError:
            yield None          # caller converts this to ": heartbeat\n\n"

        except StopAsyncIteration:
            break


@router.get("/{task_id}/stream", response_class=StreamingResponse)
async def stream_task_events(
    task_id: str,
    token: str | None = Query(None),
    last_event_id: str | None = Header(None, alias="Last-Event-ID"),
    user=Depends(get_current_user_sse),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    logger.info(
        "sse_endpoint_called",
        task_id=task_id,
        user_id=str(user.id) if user else None,
    )

    # Parse Last-Event-ID for reconnect support
    last_id: int | None = None
    if last_event_id:
        try:
            last_id = int(last_event_id)
        except ValueError:
            pass

    return StreamingResponse(
        event_generator(task_id, last_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control":    "no-cache",
            "X-Accel-Buffering": "no",        # disable Nginx/Render proxy buffering
            "Connection":       "keep-alive",
        },
    )
