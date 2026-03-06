"""
Accessibility Scanning Tasks.

Celery tasks for running accessibility scans on web pages.
Uses Playwright + axe-core for automated WCAG compliance testing.
"""

import asyncio
from datetime import datetime
from typing import Optional
from uuid import UUID

from celery import Task
from celery.signals import worker_ready
from sqlalchemy import create_engine, select, and_
from sqlalchemy.orm import Session, sessionmaker

from core.config import settings
from core.logging import get_logger
from models.evaluation import EvaluationProject
from models.finding import Finding
from models.page import Page
from models.wcag import WcagCriterion
from scanners.axe_runner import run_axe_on_page
from scanners.normalise import normalise_axe_results
from storage.client import ensure_buckets
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


@worker_ready.connect
def on_worker_ready(**kwargs):
    """
    Called when Celery worker is ready.

    Ensures MinIO buckets exist on worker startup.
    """
    logger.info("celery_worker_ready_scan_task")
    ensure_buckets()


@celery_app.task(
    bind=True,
    name="tasks.scan.scan_pages",
    queue="scan",
    max_retries=1,
    default_retry_delay=60,
)
def scan_pages(
    self: Task,
    evaluation_id: str,
    page_ids: Optional[list[str]] = None,
) -> dict:
    """
    Run accessibility scans on pages for an evaluation.

    This is a synchronous Celery task that runs async axe-core scans
    via asyncio.run().

    Args:
        evaluation_id: The evaluation UUID string
        page_ids: Optional list of specific page UUIDs to scan.
            If None or empty, scans all pages that haven't been scanned.

    Returns:
        dict with evaluation_id, pages_scanned, total_findings, pages_with_errors
    """
    logger.info(
        "scan_task_starting",
        task_id=self.request.id,
        evaluation_id=evaluation_id,
        page_ids=page_ids,
    )

    session = get_sync_session()
    total_findings = 0
    pages_with_errors = 0
    pages_scanned = 0

    try:
        # Fetch evaluation
        eval_uuid = UUID(evaluation_id)
        stmt = select(EvaluationProject).where(EvaluationProject.id == eval_uuid)
        result = session.execute(stmt)
        evaluation = result.scalar_one_or_none()

        if evaluation is None:
            raise ValueError(f"Evaluation not found: {evaluation_id}")

        # Determine which pages to scan
        if page_ids:
            # Scan specific pages
            page_uuids = [UUID(pid) for pid in page_ids]
            pages_stmt = select(Page).where(
                and_(
                    Page.evaluation_id == eval_uuid,
                    Page.id.in_(page_uuids),
                )
            )
        else:
            # Scan all pages that haven't been completed
            pages_stmt = select(Page).where(
                and_(
                    Page.evaluation_id == eval_uuid,
                    Page.scan_status != "COMPLETE",
                )
            )

        pages_result = session.execute(pages_stmt)
        pages = list(pages_result.scalars().all())

        if not pages:
            logger.info(
                "scan_no_pages_to_scan",
                evaluation_id=evaluation_id,
            )
            return {
                "evaluation_id": evaluation_id,
                "pages_scanned": 0,
                "total_findings": 0,
                "pages_with_errors": 0,
            }

        # Update evaluation status to AUDITING
        evaluation.status = "AUDITING"
        session.commit()

        logger.info(
            "scan_status_updated",
            evaluation_id=evaluation_id,
            status="AUDITING",
            pages_to_scan=len(pages),
        )

        # Build WCAG criteria map: criterion_id_string -> UUID string
        criteria_stmt = select(WcagCriterion)
        criteria_result = session.execute(criteria_stmt)
        wcag_criteria = criteria_result.scalars().all()

        wcag_criteria_map: dict[str, str] = {
            criterion.criterion_id: str(criterion.id)
            for criterion in wcag_criteria
        }

        logger.info(
            "wcag_criteria_map_built",
            criteria_count=len(wcag_criteria_map),
        )

        # Process each page
        for page in pages:
            try:
                # Update page scan status
                page.scan_status = "IN_PROGRESS"
                session.commit()

                logger.info(
                    "scan_page_starting",
                    page_id=str(page.id),
                    url=page.url,
                )

                # Run axe-core scan (async, wrapped in asyncio.run)
                axe_result = asyncio.run(
                    run_axe_on_page(
                        url=page.url,
                        evaluation_id=evaluation_id,
                        page_id=str(page.id),
                    )
                )

                # Normalize results
                normalised_findings = normalise_axe_results(
                    axe_result=axe_result,
                    evaluation_id=evaluation_id,
                    page_id=str(page.id),
                    wcag_criteria_map=wcag_criteria_map,
                )

                # Insert findings (avoid duplicates)
                page_findings_inserted = 0
                for finding_dict in normalised_findings:
                    # Check if finding already exists
                    existing_stmt = select(Finding).where(
                        and_(
                            Finding.evaluation_id == eval_uuid,
                            Finding.page_id == page.id,
                            Finding.rule_id == finding_dict["rule_id"],
                            Finding.css_selector == finding_dict["css_selector"],
                        )
                    )
                    existing_result = session.execute(existing_stmt)
                    existing_finding = existing_result.scalar_one_or_none()

                    if existing_finding is None:
                        # Create new finding
                        new_finding = Finding(
                            evaluation_id=eval_uuid,
                            page_id=page.id,
                            criterion_id=UUID(finding_dict["criterion_id"]) if finding_dict["criterion_id"] else None,
                            source=finding_dict["source"],
                            rule_id=finding_dict["rule_id"],
                            description=finding_dict["description"],
                            severity=finding_dict["severity"],
                            css_selector=finding_dict["css_selector"],
                            html_snippet=finding_dict["html_snippet"],
                            impact=finding_dict["impact"],
                            remediation=finding_dict["remediation"],
                            status=finding_dict["status"],
                            raw_result=finding_dict["raw_result"],
                            screenshot_key=finding_dict["screenshot_key"],
                        )
                        session.add(new_finding)
                        page_findings_inserted += 1

                # Update page status and screenshot
                page.scan_status = "COMPLETE"
                page.screenshot_key = axe_result.screenshot_key
                page.scanned_at = datetime.utcnow()
                session.commit()

                pages_scanned += 1
                total_findings += page_findings_inserted

                logger.info(
                    "scan_page_completed",
                    page_id=str(page.id),
                    url=page.url,
                    violations_found=len(axe_result.violations),
                    findings_inserted=page_findings_inserted,
                )

            except Exception as page_error:
                # Handle per-page errors
                logger.error(
                    "scan_page_failed",
                    page_id=str(page.id),
                    url=page.url,
                    error=str(page_error),
                )

                try:
                    page.scan_status = "FAILED"
                    session.commit()
                except Exception:
                    session.rollback()

                pages_with_errors += 1
                continue

        # Update evaluation status to REPORTING
        evaluation.status = "REPORTING"
        session.commit()

        logger.info(
            "scan_task_completed",
            task_id=self.request.id,
            evaluation_id=evaluation_id,
            pages_scanned=pages_scanned,
            total_findings=total_findings,
            pages_with_errors=pages_with_errors,
        )

        return {
            "evaluation_id": evaluation_id,
            "pages_scanned": pages_scanned,
            "total_findings": total_findings,
            "pages_with_errors": pages_with_errors,
        }

    except Exception as e:
        logger.error(
            "scan_task_failed",
            task_id=self.request.id,
            evaluation_id=evaluation_id,
            error=str(e),
        )

        # Don't change evaluation status on fatal error - leave as AUDITING
        session.rollback()
        raise

    finally:
        session.close()
