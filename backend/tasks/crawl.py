"""
Website Crawling Tasks

Tasks for crawling websites to discover pages for accessibility evaluation.
"""

from tasks import celery_app
from core.logging import get_logger

logger = get_logger(__name__)


@celery_app.task(bind=True, name="tasks.crawl.crawl_website")
def crawl_website(self, evaluation_id: str, start_url: str, max_pages: int = 15):
    """
    Crawl a website starting from the given URL.

    Args:
        evaluation_id: The evaluation this crawl belongs to
        start_url: The URL to start crawling from
        max_pages: Maximum number of pages to discover

    Returns:
        List of discovered page URLs
    """
    logger.info(
        "crawl_starting",
        evaluation_id=evaluation_id,
        start_url=start_url,
        max_pages=max_pages,
    )

    # TODO: Implement actual crawling logic with Playwright
    # This is a placeholder for Day 1

    discovered_pages = [start_url]

    logger.info(
        "crawl_completed",
        evaluation_id=evaluation_id,
        pages_found=len(discovered_pages),
    )

    return discovered_pages
