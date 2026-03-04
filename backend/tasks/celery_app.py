"""
Celery Application Export

Re-export the Celery app for worker startup.
Usage: celery -A tasks.celery_app worker --loglevel=info
"""

from tasks import celery_app

__all__ = ["celery_app"]
