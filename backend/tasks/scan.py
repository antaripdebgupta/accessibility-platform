"""
Accessibility Scanning Tasks.

Celery tasks for running accessibility scans on web pages.
Uses Playwright + axe-core for automated WCAG compliance testing.
Publishes SSE events for real-time progress updates.
"""

import asyncio
from datetime import datetime
from typing import Optional
from uuid import UUID

from celery import Task
from celery.exceptions import SoftTimeLimitExceeded
from celery.signals import worker_ready
from playwright.async_api import async_playwright
from sqlalchemy import create_engine, select, and_, func
from sqlalchemy.orm import Session, sessionmaker

from core.config import settings
from core.events import publish_task_event, make_event
from core.logging import get_logger
from models.evaluation import EvaluationProject
from models.finding import Finding
from models.page import Page
from models.wcag import WcagCriterion
from scanners.axe_runner import run_axe_on_page, AxeResult, BROWSER_ARGS
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


# ─────────────────────────────────────────────────────────────────────────────
# FIX 5: Per-page timeout protection
# ─────────────────────────────────────────────────────────────────────────────
async def scan_single_page_with_timeout(
    page_url: str,
    evaluation_id: str,
    page_id: str,
    context,
    timeout_seconds: int = 45,
) -> AxeResult:
    """
    Scan a single page with a hard timeout.

    Wraps run_axe_on_page in asyncio.wait_for so one hanging page
    cannot stall the entire scan task.

    Args:
        page_url: URL to scan
        evaluation_id: Evaluation UUID string
        page_id: Page UUID string
        context: Shared Playwright BrowserContext
        timeout_seconds: Maximum time allowed for this page scan

    Returns:
        AxeResult, potentially with scan_failed=True on timeout
    """
    try:
        return await asyncio.wait_for(
            run_axe_on_page(page_url, evaluation_id, page_id, context=context),
            timeout=timeout_seconds,
        )
    except asyncio.TimeoutError:
        logger.error(
            "page_scan_timeout",
            url=page_url,
            timeout=timeout_seconds,
        )
        return AxeResult(
            violations=[],
            passes=[],
            incomplete=[],
            url=page_url,
            screenshot_key=None,
            scan_failed=True,
            failure_reason=f"scan timeout after {timeout_seconds}s",
        )


# ─────────────────────────────────────────────────────────────────────────────
# FIX 4: Browser context reuse — single browser for entire scan
# ─────────────────────────────────────────────────────────────────────────────
async def scan_all_pages_async(
    pages_data: list[tuple[str, str, str]],
    evaluation_id: str,
    wcag_criteria_map: dict[str, str],
) -> list[tuple[str, AxeResult]]:
    """
    Scan all pages using a single shared browser context.

    This is the key performance optimization — launching one browser
    instead of one per page saves 2-4 seconds per page.

    Args:
        pages_data: List of (page_id, url, page_id) tuples
        evaluation_id: Evaluation UUID string
        wcag_criteria_map: WCAG criterion mapping

    Returns:
        List of (page_id, AxeResult) tuples
    """
    results = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=BROWSER_ARGS,
        )

        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 (compatible; A11yBot/1.0)",
            ignore_https_errors=True,
            java_script_enabled=True,
        )

        logger.info(
            "scan_browser_launched",
            evaluation_id=evaluation_id,
            pages_count=len(pages_data),
        )

        try:
            for page_id, url, _ in pages_data:
                result = await scan_single_page_with_timeout(
                    page_url=url,
                    evaluation_id=evaluation_id,
                    page_id=page_id,
                    context=context,
                    timeout_seconds=45,
                )
                results.append((page_id, result))
        finally:
            await context.close()
            await browser.close()

    return results


@worker_ready.connect
def on_worker_ready(**kwargs):
    """
    Called when Celery worker is ready.

    Ensures MinIO buckets exist on worker startup.
    """
    logger.info("celery_worker_ready_scan_task")
    try:
        ensure_buckets()
        logger.info("celery_worker_storage_initialized_successfully")
    except Exception as e:
        logger.error("celery_worker_storage_initialization_failed", error=str(e))


@celery_app.task(
    bind=True,
    name="tasks.scan.scan_pages",
    queue="scan",
    max_retries=1,
    default_retry_delay=60,
    soft_time_limit=300,  # 5 min soft limit — raises SoftTimeLimitExceeded
    time_limit=360,       # 6 min hard limit — kills the task
)
def scan_pages(
    self: Task,
    evaluation_id: str,
    page_ids: Optional[list[str]] = None,
) -> dict:
    """
    Run accessibility scans on pages for an evaluation.

    This task uses a single shared browser context for all pages,
    dramatically reducing scan time (saves 2-4 seconds per page).
    Publishes SSE events for real-time progress updates.

    Args:
        evaluation_id: The evaluation UUID string
        page_ids: Optional list of specific page UUIDs to scan.
            If None or empty, scans all pages that haven't been scanned.

    Returns:
        dict with evaluation_id, pages_scanned, total_findings, pages_with_errors
    """
    task_id = self.request.id

    logger.info(
        "scan_task_starting",
        task_id=task_id,
        evaluation_id=evaluation_id,
        page_ids=page_ids,
    )

    session = get_sync_session()
    total_findings = 0
    pages_with_errors = 0
    pages_scanned = 0
    unscanned_pages: list[Page] = []

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
            # Scan specific pages (including SCAN_ERROR pages for retry)
            page_uuids = [UUID(pid) for pid in page_ids]
            pages_stmt = select(Page).where(
                and_(
                    Page.evaluation_id == eval_uuid,
                    Page.id.in_(page_uuids),
                )
            )
        else:
            # Scan only pages that are in the sample and haven't been completed
            # WCAG-EM Step 3: Only scan pages selected through sampling algorithm
            pages_stmt = select(Page).where(
                and_(
                    Page.evaluation_id == eval_uuid,
                    Page.in_sample == True,  # noqa: E712 - Only scan sampled pages
                    Page.scan_status.notin_(["COMPLETE"]),
                )
            )

        pages_result = session.execute(pages_stmt)
        pages = list(pages_result.scalars().all())

        if not pages:
            # Check if there are any sampled pages at all
            sampled_count_stmt = select(func.count()).select_from(Page).where(
                and_(
                    Page.evaluation_id == eval_uuid,
                    Page.in_sample == True,  # noqa: E712
                )
            )
            sampled_result = session.execute(sampled_count_stmt)
            sampled_count = sampled_result.scalar() or 0

            if sampled_count == 0:
                logger.error(
                    "scan_no_sampled_pages",
                    evaluation_id=evaluation_id,
                )
                raise ValueError(
                    "No pages in sample. Run sampling before scanning. "
                    "Use POST /evaluations/{id}/sample to compute the sample."
                )

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

        # Get total discovered pages for logging
        total_pages_stmt = select(func.count()).select_from(Page).where(
            Page.evaluation_id == eval_uuid
        )
        total_result = session.execute(total_pages_stmt)
        total_discovered = total_result.scalar() or 0

        logger.info(
            "scan_sample_pages",
            evaluation_id=evaluation_id,
            sampled_pages=len(pages),
            total_discovered=total_discovered,
            message=f"Scanning {len(pages)} sampled pages out of {total_discovered} discovered",
        )

        # Track unscanned pages for SoftTimeLimitExceeded handling
        unscanned_pages = pages.copy()

        # Update evaluation status to AUDITING
        evaluation.status = "AUDITING"
        session.commit()

        logger.info(
            "scan_status_updated",
            evaluation_id=evaluation_id,
            status="AUDITING",
            pages_to_scan=len(pages),
        )

        # Publish: Scan started
        publish_task_event(task_id, make_event("progress", {
            "step": "started",
            "message": "Scan started",
            "pages_total": len(pages),
            "pages_scanned": 0,
            "percent": 0,
            "evaluation_id": evaluation_id,
        }))

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

        # Mark all pages as IN_PROGRESS before starting batch scan
        for page in pages:
            page.scan_status = "IN_PROGRESS"
        session.commit()

        # ─────────────────────────────────────────────────────────────────────
        # FIX 4 & 5: Run all scans with shared browser context
        # ─────────────────────────────────────────────────────────────────────
        pages_data = [(str(page.id), page.url, str(page.id)) for page in pages]
        total_pages = len(pages)

        # Run async scan with shared browser
        scan_results = asyncio.run(
            scan_all_pages_async(pages_data, evaluation_id, wcag_criteria_map)
        )

        # Build lookup for results
        results_map = {page_id: result for page_id, result in scan_results}

        # Process each page's results
        for page_index, page in enumerate(pages):
            page_id_str = str(page.id)
            axe_result = results_map.get(page_id_str)

            # Publish: Scanning page event (before processing)
            publish_task_event(task_id, make_event("progress", {
                "step": "scanning_page",
                "message": f"Scanning: {page.url}",
                "current_page": page.url,
                "pages_scanned": page_index,
                "pages_total": total_pages,
                "percent": int((page_index / total_pages) * 100),
                "evaluation_id": evaluation_id,
            }))

            # Remove from unscanned list
            if page in unscanned_pages:
                unscanned_pages.remove(page)

            if axe_result is None:
                # Should not happen, but handle gracefully
                logger.error(
                    "scan_result_missing",
                    page_id=page_id_str,
                    url=page.url,
                )
                page.scan_status = "SCAN_ERROR"
                pages_with_errors += 1
                session.commit()
                continue

            # ─────────────────────────────────────────────────────────────────
            # FIX 2: Handle scan_failed — set SCAN_ERROR, never store as success
            # ─────────────────────────────────────────────────────────────────
            if axe_result.scan_failed:
                page.scan_status = "SCAN_ERROR"
                page.screenshot_key = axe_result.screenshot_key
                page.scanned_at = datetime.utcnow()
                session.commit()
                pages_with_errors += 1

                logger.info(
                    "page_scan_result",
                    url=page.url,
                    status="error",
                    findings_inserted=0,
                    failure_reason=axe_result.failure_reason,
                )
                continue

            # Normalize results
            normalised_findings = normalise_axe_results(
                axe_result=axe_result,
                evaluation_id=evaluation_id,
                page_id=page_id_str,
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

            # ─────────────────────────────────────────────────────────────────
            # FIX 8: Log summary after each page
            # ─────────────────────────────────────────────────────────────────
            logger.info(
                "page_scan_result",
                url=page.url,
                status="success",
                findings_inserted=page_findings_inserted,
                failure_reason=None,
            )

            # Publish: Page complete event
            publish_task_event(task_id, make_event("progress", {
                "step": "page_complete",
                "message": f"Scanned {page.url} — {page_findings_inserted} issues found",
                "last_page": page.url,
                "findings_on_page": page_findings_inserted,
                "pages_scanned": pages_scanned,
                "pages_total": total_pages,
                "percent": int((pages_scanned / total_pages) * 100),
                "evaluation_id": evaluation_id,
            }))

        # Update evaluation status to REPORTING
        evaluation.status = "REPORTING"
        session.commit()

        logger.info(
            "scan_task_completed",
            task_id=task_id,
            evaluation_id=evaluation_id,
            pages_scanned=pages_scanned,
            total_findings=total_findings,
            pages_with_errors=pages_with_errors,
        )

        # Publish: Scan complete event
        publish_task_event(task_id, make_event("complete", {
            "step": "complete",
            "message": f"Scan complete — {total_findings} issues found across {pages_scanned} pages",
            "total_findings": total_findings,
            "pages_scanned": pages_scanned,
            "pages_with_errors": pages_with_errors,
            "evaluation_id": evaluation_id,
        }))

        return {
            "evaluation_id": evaluation_id,
            "pages_scanned": pages_scanned,
            "total_findings": total_findings,
            "pages_with_errors": pages_with_errors,
        }

    # ─────────────────────────────────────────────────────────────────────────
    # FIX 7: SoftTimeLimitExceeded handling — advance with partial results
    # ─────────────────────────────────────────────────────────────────────────
    except SoftTimeLimitExceeded:
        logger.error(
            "scan_soft_time_limit_exceeded",
            task_id=task_id,
            evaluation_id=evaluation_id,
            unscanned_pages_count=len(unscanned_pages),
        )

        # Publish: Error event for timeout
        publish_task_event(task_id, make_event("error", {
            "step": "timeout",
            "message": f"Scan timed out. {len(unscanned_pages)} pages were not scanned.",
            "pages_scanned": pages_scanned,
            "unscanned_count": len(unscanned_pages),
            "evaluation_id": evaluation_id,
        }))

        try:
            # Mark remaining pages as SCAN_ERROR
            for page in unscanned_pages:
                page.scan_status = "SCAN_ERROR"
            session.commit()

            # Still advance to REPORTING with partial results
            eval_uuid = UUID(evaluation_id)
            stmt = select(EvaluationProject).where(EvaluationProject.id == eval_uuid)
            result = session.execute(stmt)
            evaluation = result.scalar_one_or_none()
            if evaluation:
                evaluation.status = "REPORTING"
                session.commit()

            logger.info(
                "scan_advanced_to_reporting_with_partial_results",
                evaluation_id=evaluation_id,
                pages_scanned=pages_scanned,
                pages_with_errors=len(unscanned_pages),
            )
        except Exception as cleanup_error:
            logger.error(
                "scan_timeout_cleanup_failed",
                error=str(cleanup_error),
            )
            session.rollback()

        return {
            "evaluation_id": evaluation_id,
            "pages_scanned": pages_scanned,
            "total_findings": total_findings,
            "pages_with_errors": len(unscanned_pages),
            "timeout": True,
        }

    except Exception as e:
        logger.error(
            "scan_task_failed",
            task_id=task_id,
            evaluation_id=evaluation_id,
            error=str(e),
        )

        # Publish: Error event
        publish_task_event(task_id, make_event("error", {
            "step": "error",
            "message": str(e),
            "evaluation_id": evaluation_id,
        }))

        # Don't change evaluation status on fatal error - leave as AUDITING
        session.rollback()
        raise

    finally:
        session.close()
