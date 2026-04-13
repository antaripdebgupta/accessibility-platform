"""
Redis Pub/Sub Event Bus for SSE.

Provides event publishing (sync) for Celery tasks and event subscribing (async)
for FastAPI SSE endpoints. Events flow from Celery workers through Redis
pub/sub to connected browser clients.

Architecture:
    Celery Worker -> Redis pub/sub -> FastAPI SSE -> Browser EventSource
"""

import asyncio
import json
from datetime import datetime
from typing import Any, AsyncGenerator, Optional

import redis
import redis.asyncio as aioredis

from core.config import settings
from core.logging import get_logger

logger = get_logger(__name__)

# Constants
CHANNEL_PREFIX = "task:"
SSE_TIMEOUT_SECONDS = 30  # Timeout for waiting on individual messages
SSE_MAX_DURATION_SECONDS = 1800  # 30 minutes max connection duration
HEARTBEAT_INTERVAL_SECONDS = 30  # Send heartbeat to keep connection alive


def make_event(event_type: str, data: dict) -> dict:
    """
    Build a standard SSE event dict.

    Args:
        event_type: Event type - "progress" | "complete" | "error" | "heartbeat"
        data: Arbitrary dict with event payload

    Returns:
        Standardized event dict with type, data, and timestamp
    """
    return {
        "type": event_type,
        "data": data,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


def publish_task_event(task_id: str, event: dict) -> None:
    """
    Publish a task progress event to Redis pub/sub.

    Called from Celery tasks (synchronous context). This function is
    designed to be non-blocking and fail-safe - a Redis failure must
    never crash the Celery task.

    Args:
        task_id: The Celery task ID
        event: Event dict (must be JSON serializable)

    Note:
        - Creates a new Redis connection per publish (connection pooling
          is handled by redis-py internally)
        - Automatically adds task_id to the event
        - Wraps entire function in try/except - never raises
    """
    try:
        # Add task_id to event for client reference
        event_with_id = {**event, "task_id": task_id}

        # Create synchronous Redis client
        client = redis.Redis.from_url(
            settings.redis_url,
            decode_responses=True,
            socket_timeout=5.0,
            socket_connect_timeout=5.0,
        )

        try:
            # Publish to task-specific channel
            channel = f"{CHANNEL_PREFIX}{task_id}"
            message = json.dumps(event_with_id)
            client.publish(channel, message)

            logger.debug(
                "sse_event_published",
                task_id=task_id,
                event_type=event.get("type"),
                channel=channel,
            )
        finally:
            # Always close the client connection
            client.close()

    except Exception as e:
        # Log the error but never raise - task execution must continue
        logger.warning(
            "sse_event_publish_failed",
            task_id=task_id,
            event_type=event.get("type"),
            error=str(e),
        )


async def subscribe_task_events(task_id: str) -> AsyncGenerator[Any, None]:
    """
    Async generator that yields event dicts from Redis pub/sub.

    Subscribes to channel "task:{task_id}" and yields each message
    as a parsed dict. Automatically handles:
    - 30-second message timeout (yields heartbeat to keep connection alive)
    - 30-minute maximum connection duration
    - Clean resource cleanup on exit

    Args:
        task_id: The Celery task ID to subscribe to

    Yields:
        Event dicts from Redis pub/sub

    Note:
        Generator stops when:
        - Event with type "complete" or "error" is received
        - 30-minute total duration exceeded
        - Connection error occurs
    """
    client: Optional[aioredis.Redis] = None
    pubsub = None  # Type: redis.asyncio PubSub
    start_time = datetime.utcnow()
    channel = f"{CHANNEL_PREFIX}{task_id}"

    try:
        # Create async Redis client
        client = await aioredis.from_url(
            settings.redis_url,
            decode_responses=True,
            socket_timeout=5.0,
            socket_connect_timeout=5.0,
        )

        # Create pub/sub instance and subscribe
        pubsub = client.pubsub()
        await pubsub.subscribe(channel)

        logger.info(
            "sse_subscription_started",
            task_id=task_id,
            channel=channel,
        )

        while True:
            # Check total connection duration
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            if elapsed >= SSE_MAX_DURATION_SECONDS:
                logger.info(
                    "sse_max_duration_reached",
                    task_id=task_id,
                    elapsed_seconds=elapsed,
                )
                yield make_event("timeout", {
                    "message": "Maximum connection duration reached",
                    "elapsed_seconds": elapsed,
                })
                break

            try:
                # Wait for message with timeout
                message = await asyncio.wait_for(
                    pubsub.get_message(ignore_subscribe_messages=True),
                    timeout=SSE_TIMEOUT_SECONDS,
                )

                if message is not None and message.get("type") == "message":
                    # Parse the JSON message
                    try:
                        data = message.get("data")
                        if isinstance(data, str):
                            event = json.loads(data)
                        elif isinstance(data, dict):
                            event = data
                        else:
                            # Skip non-dict data
                            continue

                        yield event

                        # Check for terminal event types
                        event_type = event.get("type") if isinstance(event, dict) else None
                        if event_type in ("complete", "error"):
                            logger.info(
                                "sse_terminal_event_received",
                                task_id=task_id,
                                event_type=event_type,
                            )
                            break

                    except json.JSONDecodeError as e:
                        logger.warning(
                            "sse_invalid_json",
                            task_id=task_id,
                            error=str(e),
                            raw_data=str(message.get("data"))[:100],
                        )
                        # Continue listening - don't break on invalid JSON

            except asyncio.TimeoutError:
                # No message received within timeout - send heartbeat
                logger.debug(
                    "sse_heartbeat_sent",
                    task_id=task_id,
                )
                yield make_event("heartbeat", {
                    "message": "Connection alive",
                    "elapsed_seconds": int(elapsed),
                })
                # Continue listening

    except asyncio.CancelledError:
        # Client disconnected - clean exit
        logger.info(
            "sse_subscription_cancelled",
            task_id=task_id,
        )
        raise

    except Exception as e:
        logger.error(
            "sse_subscription_error",
            task_id=task_id,
            error=str(e),
        )
        yield make_event("error", {
            "message": f"Subscription error: {str(e)}",
        })

    finally:
        # Clean up resources
        if pubsub is not None:
            try:
                await pubsub.unsubscribe(channel)
                await pubsub.close()
                logger.debug(
                    "sse_pubsub_closed",
                    task_id=task_id,
                )
            except Exception as e:
                logger.warning(
                    "sse_pubsub_cleanup_error",
                    task_id=task_id,
                    error=str(e),
                )

        if client is not None:
            try:
                await client.aclose()
                logger.debug(
                    "sse_client_closed",
                    task_id=task_id,
                )
            except Exception as e:
                logger.warning(
                    "sse_client_cleanup_error",
                    task_id=task_id,
                    error=str(e),
                )
