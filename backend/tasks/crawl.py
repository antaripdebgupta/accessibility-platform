"""
Website Crawling Tasks

Celery tasks for crawling websites to discover pages for accessibility evaluation.
Uses Playwright spider for async crawling with synchronous DB operations.
Publishes SSE events for real-time progress updates.
"""

import asyncio
from datetime import datetime
from uuid import UUID

from celery import Task
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from core.config import settings
from core.events import publish_task_event, make_event
from core.logging import get_logger
from crawler.spider import crawl as spider_crawl
from models.evaluation import EvaluationProject
from models.page import Page
from tasks import celery_app

logger = get_logger(__name__)


def get_sync_database_url() -> str:
    """
    Convert async database URL to sync format for Celery tasks.
    Replaces postgresql+asyncpg:// with postgresql+psycopg2://
    """
    db_url = settings.database_url
    if "asyncpg" in db_url:
        return db_url.replace("postgresql+asyncpg", "postgresql+psycopg2")
    return db_url


# Create synchronous engine for Celery tasks
sync_engine = create_engine(
    get_sync_database_url(),
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)

SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


def get_sync_session() -> Session:
    """Get a synchronous database session for Celery tasks."""
    return SyncSessionLocal()


@celery_app.task(
    bind=True,
    name="tasks.crawl.crawl_website",
    queue="crawl",
    max_retries=2,
    default_retry_delay=30,
    autoretry_for=(Exception,),
    retry_backoff=True,
)
def crawl_website(
    self: Task,
    evaluation_id: str,
    target_url: str,
    max_pages: int = 15,
    respect_robots: bool = True
) -> dict:
    """
    Crawl a website starting from the given URL.

    This is a synchronous Celery task that runs the async spider
    via asyncio.run(). Publishes SSE events for real-time progress.

    Args:
        evaluation_id: The evaluation UUID this crawl belongs to
        target_url: The URL to start crawling from
        max_pages: Maximum number of pages to discover
        respect_robots: Whether to respect robots.txt

    Returns:
        dict with pages_found count and evaluation_id
    """
    task_id = self.request.id

    logger.info(
        "crawl_task_starting",
        task_id=task_id,
        evaluation_id=evaluation_id,
        target_url=target_url,
        max_pages=max_pages,
        respect_robots=respect_robots,
    )

    # Publish: Task started
    publish_task_event(task_id, make_event("progress", {
        "step": "started",
        "message": "Crawl started",
        "pages_found": 0,
        "evaluation_id": evaluation_id,
    }))

    session = get_sync_session()

    try:
        # Fetch evaluation
        eval_uuid = UUID(evaluation_id)
        stmt = select(EvaluationProject).where(EvaluationProject.id == eval_uuid)
        result = session.execute(stmt)
        evaluation = result.scalar_one_or_none()

        if evaluation is None:
            raise ValueError(f"Evaluation not found: {evaluation_id}")

        # Update status to EXPLORING
        evaluation.status = "EXPLORING"
        session.commit()

        logger.info(
            "crawl_status_updated",
            evaluation_id=evaluation_id,
            status="EXPLORING"
        )

        # Publish: Browser launching
        publish_task_event(task_id, make_event("progress", {
            "step": "exploring",
            "message": "Browser launched, crawling pages...",
            "pages_found": 0,
            "evaluation_id": evaluation_id,
        }))

        # Run the async spider synchronously
        crawl_results = asyncio.run(
            spider_crawl(
                start_url=target_url,
                max_pages=max_pages,
                respect_robots=respect_robots
            )
        )

        logger.info(
            "crawl_spider_completed",
            evaluation_id=evaluation_id,
            pages_found=len(crawl_results)
        )

        # Insert discovered pages into database
        pages_inserted = 0
        for page_data in crawl_results:
            # Check if page already exists (idempotent)
            existing_stmt = select(Page).where(
                Page.evaluation_id == eval_uuid,
                Page.url == page_data.url
            )
            existing_result = session.execute(existing_stmt)
            existing_page = existing_result.scalar_one_or_none()

            if existing_page is None:
                # Insert new page
                new_page = Page(
                    evaluation_id=eval_uuid,
                    url=page_data.url,
                    title=page_data.title or None,
                    page_type=page_data.page_type,
                    http_status=page_data.http_status if page_data.http_status > 0 else None,
                    crawl_status="COMPLETE" if page_data.error is None else "FAILED",
                    scan_status="PENDING",
                    discovered_at=datetime.utcnow(),
                )
                session.add(new_page)
                pages_inserted += 1

                # Publish: Page found event
                publish_task_event(task_id, make_event("progress", {
                    "step": "page_found",
                    "message": f"Found: {page_data.url}",
                    "pages_found": pages_inserted,
                    "url": page_data.url,
                    "page_type": page_data.page_type,
                    "page_title": page_data.title,
                    "evaluation_id": evaluation_id,
                    "percent": min(95, int((pages_inserted / max_pages) * 100)),
                }))

        # Commit all new pages
        session.commit()

        # Update evaluation status to SAMPLING
        evaluation.status = "SAMPLING"
        session.commit()

        logger.info(
            "crawl_task_completed",
            task_id=task_id,
            evaluation_id=evaluation_id,
            pages_found=len(crawl_results),
            pages_inserted=pages_inserted
        )

        # Publish: Crawl complete
        publish_task_event(task_id, make_event("complete", {
            "step": "complete",
            "message": f"Crawl complete — {len(crawl_results)} pages discovered",
            "pages_found": len(crawl_results),
            "pages_inserted": pages_inserted,
            "evaluation_id": evaluation_id,
        }))

        return {
            "pages_found": len(crawl_results),
            "pages_inserted": pages_inserted,
            "evaluation_id": evaluation_id,
        }

    except Exception as e:
        logger.error(
            "crawl_task_failed",
            task_id=task_id,
            evaluation_id=evaluation_id,
            error=str(e),
            retry_count=self.request.retries,
        )

        # Publish: Error event
        publish_task_event(task_id, make_event("error", {
            "step": "error",
            "message": str(e),
            "evaluation_id": evaluation_id,
        }))

        # Reset evaluation status to DRAFT on failure
        try:
            stmt = select(EvaluationProject).where(
                EvaluationProject.id == UUID(evaluation_id)
            )
            result = session.execute(stmt)
            evaluation = result.scalar_one_or_none()
            if evaluation and evaluation.status == "EXPLORING":
                evaluation.status = "DRAFT"
                session.commit()
        except Exception as reset_error:
            logger.error(
                "crawl_status_reset_failed",
                evaluation_id=evaluation_id,
                error=str(reset_error)
            )

        # Re-raise for Celery retry mechanism
        raise self.retry(exc=e)

    finally:
        session.close()
