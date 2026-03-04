"""
Celery Application Configuration

This module initializes the Celery app for background task processing.
Tasks include: website crawling, accessibility scanning, and PDF report generation.
"""

from celery import Celery

from core.config import settings

# ─────────────────────────────────────────────────────────────────────────────
# Celery Application
# ─────────────────────────────────────────────────────────────────────────────

celery_app = Celery(
    "accessibility_platform",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "tasks.crawl",
        "tasks.scan",
        "tasks.report",
    ],
)

# ─────────────────────────────────────────────────────────────────────────────
# Celery Configuration
# ─────────────────────────────────────────────────────────────────────────────

celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,

    # Result backend settings
    result_expires=3600,  # Results expire after 1 hour

    # Task execution settings
    task_acks_late=True,  # Acknowledge tasks after execution
    task_reject_on_worker_lost=True,

    # Worker settings
    worker_prefetch_multiplier=1,  # One task at a time per worker
    worker_max_tasks_per_child=100,  # Restart worker after 100 tasks

    # Task routing
    task_routes={
        "tasks.crawl.*": {"queue": "crawl"},
        "tasks.scan.*": {"queue": "scan"},
        "tasks.report.*": {"queue": "report"},
    },

    # Default queue
    task_default_queue="scan",

    # Rate limiting
    task_annotations={
        "tasks.crawl.crawl_website": {"rate_limit": "5/m"},
        "tasks.scan.run_accessibility_scan": {"rate_limit": "10/m"},
    },
)

# ─────────────────────────────────────────────────────────────────────────────
# Task beat schedule (for periodic tasks)
# ─────────────────────────────────────────────────────────────────────────────

# Uncomment to enable periodic tasks (requires celery beat)
# celery_app.conf.beat_schedule = {
#     "cleanup-old-reports": {
#         "task": "tasks.report.cleanup_old_reports",
#         "schedule": 86400,  # Daily
#     },
# }
