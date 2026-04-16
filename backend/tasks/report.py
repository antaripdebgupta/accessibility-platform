"""
Report Generation Celery Tasks.

Tasks for generating PDF, EARL, and CSV accessibility reports.
Handles the complete report generation workflow including:
- Verdict computation
- Template rendering
- PDF generation with WeasyPrint
- EARL JSON-LD export
- CSV export
- MinIO storage upload
Publishes SSE events for real-time progress updates.
"""

import json
from datetime import datetime
from typing import Optional
from uuid import UUID

from celery import Task
from sqlalchemy import select, and_

from core.events import publish_task_event, make_event
from core.logging import get_logger
from db.sync_engine import get_sync_session
from models.audit_log import AuditLog
from models.evaluation import EvaluationProject
from models.finding import Finding
from models.page import Page
from models.report import Report
from models.wcag import WcagCriterion
from reports.csv_export import generate_csv
from reports.earl_export import generate_earl
from reports.generator import generate_pdf_report, ReportGenerationError
from reports.verdict import compute_verdict
from storage.client import ensure_buckets
from storage.operations import upload_bytes
from tasks import celery_app
from longitudinal.series import register_evaluation_in_series_sync
from sqlalchemy.orm import Session
from core.config import settings

logger = get_logger(__name__)


def log_audit_action_sync(
    session: Session,
    action: str,
    entity_type: str,
    entity_id: str,
    organisation_id: str,
    after_state: Optional[dict] = None,
) -> None:
    """
    Log an audit action synchronously.

    This is a synchronous version of log_action for use in Celery tasks.
    """
    try:
        audit_log = AuditLog(
            user_id=None,  # System action
            organisation_id=UUID(organisation_id) if organisation_id else None,
            action=action,
            entity_type=entity_type,
            entity_id=UUID(entity_id) if entity_id else None,
            before_state=None,
            after_state=after_state,
            ip_address=None,
        )
        session.add(audit_log)
    except Exception as e:
        logger.error(
            "audit_log_failed",
            action=action,
            entity_id=entity_id,
            error=str(e),
        )


@celery_app.task(
    bind=True,
    name="tasks.report.generate_report",
    queue="report",
    max_retries=1,
    default_retry_delay=60,
)
def generate_report(
    self: Task,
    evaluation_id: str,
    report_types: Optional[list[str]] = None,
    include_dismissed: bool = False,
) -> dict:
    """
    Generate accessibility reports for an evaluation.

    This is a synchronous Celery task that generates PDF, EARL, and CSV
    reports and uploads them to MinIO storage. Publishes SSE events for
    real-time progress updates.

    Args:
        evaluation_id: The evaluation UUID string
        report_types: List of report types to generate (full, earl, csv)
            If None, defaults to ["full", "earl", "csv"]
        include_dismissed: Whether to include dismissed findings

    Returns:
        dict with evaluation_id, reports_generated, verdict, criteria_failed, total_findings
    """
    task_id = self.request.id

    logger.info(
        "report_generation_starting",
        task_id=task_id,
        evaluation_id=evaluation_id,
        report_types=report_types,
        include_dismissed=include_dismissed,
    )

    # Publish: Report generation started
    publish_task_event(task_id, make_event("progress", {
        "step": "started",
        "message": "Report generation started",
        "evaluation_id": evaluation_id,
    }))

    # Ensure MinIO buckets exist
    ensure_buckets()

    # Default report types
    if report_types is None:
        report_types = ["full", "earl", "csv"]

    session = get_sync_session()

    try:
        # Step 1: Fetch evaluation
        eval_uuid = UUID(evaluation_id)
        stmt = select(EvaluationProject).where(EvaluationProject.id == eval_uuid)
        result = session.execute(stmt)
        evaluation = result.scalar_one_or_none()

        if evaluation is None:
            raise ValueError(f"Evaluation not found: {evaluation_id}")

        # Step 2: Update evaluation status to REPORTING
        evaluation.status = "REPORTING"
        session.commit()

        logger.info(
            "report_status_updated",
            evaluation_id=evaluation_id,
            status="REPORTING",
        )

        # Step 3: Fetch confirmed findings with page and criterion
        status_filter = ["CONFIRMED"]
        if include_dismissed:
            status_filter.append("DISMISSED")

        findings_stmt = (
            select(Finding)
            .where(
                and_(
                    Finding.evaluation_id == eval_uuid,
                    Finding.status.in_(status_filter),
                )
            )
            .order_by(Finding.created_at)
        )
        findings_result = session.execute(findings_stmt)
        confirmed_findings = list(findings_result.scalars().all())

        # Load related pages and criteria
        page_ids = {f.page_id for f in confirmed_findings}
        criterion_ids = {f.criterion_id for f in confirmed_findings if f.criterion_id}

        pages_map = {}
        if page_ids:
            pages_stmt = select(Page).where(Page.id.in_(page_ids))
            pages_result = session.execute(pages_stmt)
            pages_map = {p.id: p for p in pages_result.scalars().all()}

        criteria_map = {}
        if criterion_ids:
            criteria_stmt = select(WcagCriterion).where(WcagCriterion.id.in_(criterion_ids))
            criteria_result = session.execute(criteria_stmt)
            criteria_map = {c.id: c for c in criteria_result.scalars().all()}

        # Attach page and criterion to findings for export functions
        for finding in confirmed_findings:
            if finding.page_id and finding.page_id in pages_map:
                finding.page = pages_map[finding.page_id]
            if finding.criterion_id and finding.criterion_id in criteria_map:
                finding.criterion = criteria_map[finding.criterion_id]

        # Sort by criterion code, then severity
        severity_order = {"critical": 0, "serious": 1, "moderate": 2, "minor": 3, "info": 4}
        confirmed_findings.sort(
            key=lambda f: (
                f.criterion.criterion_id if f.criterion else "zzz",
                severity_order.get(f.severity or "moderate", 5),
            )
        )

        logger.info(
            "report_findings_fetched",
            evaluation_id=evaluation_id,
            findings_count=len(confirmed_findings),
        )

        # Step 4: Compute verdict
        verdict = compute_verdict(evaluation_id, session, evaluation.conformance_level)

        logger.info(
            "report_verdict_computed",
            evaluation_id=evaluation_id,
            verdict=verdict.verdict,
            criteria_passed=verdict.criteria_passed,
            criteria_failed=verdict.criteria_failed,
            total_findings=verdict.total_findings,
        )

        # Publish: Verdict computed event
        publish_task_event(task_id, make_event("progress", {
            "step": "verdict_computed",
            "message": f"Conformance verdict: {verdict.verdict}",
            "verdict": verdict.verdict,
            "criteria_passed": verdict.criteria_passed,
            "criteria_failed": verdict.criteria_failed,
            "total_findings": verdict.total_findings,
            "evaluation_id": evaluation_id,
        }))

        # Step 5: Generate reports
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        reports_generated = []

        for report_type in report_types:
            try:
                if report_type == "full":
                    # Generate PDF report
                    pdf_bytes = generate_pdf_report(verdict, evaluation, confirmed_findings)
                    storage_key = f"reports/{evaluation_id}/full_{timestamp}.pdf"
                    upload_bytes(
                        bucket=settings.minio_bucket_reports,
                        key=storage_key,
                        data=pdf_bytes,
                        content_type="application/pdf",
                    )

                    # Create Report record
                    report = Report(
                        evaluation_id=eval_uuid,
                        report_type="full",
                        conformance_verdict=verdict.verdict,
                        criteria_passed=verdict.criteria_passed,
                        criteria_failed=verdict.criteria_failed,
                        criteria_na=verdict.criteria_na,
                        total_findings=verdict.total_findings,
                        storage_key=storage_key,
                    )
                    session.add(report)
                    reports_generated.append("full")

                    logger.info(
                        "report_pdf_generated",
                        evaluation_id=evaluation_id,
                        storage_key=storage_key,
                        size=len(pdf_bytes),
                    )

                    # Publish: Full PDF generated event
                    publish_task_event(task_id, make_event("progress", {
                        "step": "full_generated",
                        "message": "PDF report generated",
                        "report_type": "full",
                        "evaluation_id": evaluation_id,
                    }))

                elif report_type == "earl":
                    # Generate EARL JSON-LD
                    earl_dict = generate_earl(evaluation, confirmed_findings, verdict)
                    earl_bytes = json.dumps(earl_dict, indent=2, ensure_ascii=False).encode("utf-8")
                    storage_key = f"reports/{evaluation_id}/earl_{timestamp}.json"
                    upload_bytes(
                        bucket=settings.minio_bucket_reports,
                        key=storage_key,
                        data=earl_bytes,
                        content_type="application/ld+json",
                    )

                    # Create Report record
                    report = Report(
                        evaluation_id=eval_uuid,
                        report_type="earl",
                        conformance_verdict=verdict.verdict,
                        criteria_passed=verdict.criteria_passed,
                        criteria_failed=verdict.criteria_failed,
                        criteria_na=verdict.criteria_na,
                        total_findings=verdict.total_findings,
                        storage_key=storage_key,
                    )
                    session.add(report)
                    reports_generated.append("earl")

                    logger.info(
                        "report_earl_generated",
                        evaluation_id=evaluation_id,
                        storage_key=storage_key,
                        size=len(earl_bytes),
                    )

                    # Publish: EARL generated event
                    publish_task_event(task_id, make_event("progress", {
                        "step": "earl_generated",
                        "message": "EARL JSON-LD generated",
                        "report_type": "earl",
                        "evaluation_id": evaluation_id,
                    }))

                elif report_type == "csv":
                    # Generate CSV
                    csv_bytes = generate_csv(confirmed_findings)
                    storage_key = f"reports/{evaluation_id}/findings_{timestamp}.csv"
                    upload_bytes(
                        bucket=settings.minio_bucket_reports,
                        key=storage_key,
                        data=csv_bytes,
                        content_type="text/csv",
                    )

                    # Create Report record
                    report = Report(
                        evaluation_id=eval_uuid,
                        report_type="csv",
                        conformance_verdict=verdict.verdict,
                        criteria_passed=verdict.criteria_passed,
                        criteria_failed=verdict.criteria_failed,
                        criteria_na=verdict.criteria_na,
                        total_findings=verdict.total_findings,
                        storage_key=storage_key,
                    )
                    session.add(report)
                    reports_generated.append("csv")

                    # Publish: CSV generated event
                    publish_task_event(task_id, make_event("progress", {
                        "step": "csv_generated",
                        "message": "CSV export generated",
                        "report_type": "csv",
                        "evaluation_id": evaluation_id,
                    }))

                    logger.info(
                        "report_csv_generated",
                        evaluation_id=evaluation_id,
                        storage_key=storage_key,
                        size=len(csv_bytes),
                    )

                else:
                    logger.warning(
                        "report_unknown_type",
                        evaluation_id=evaluation_id,
                        report_type=report_type,
                    )

            except ReportGenerationError as e:
                logger.error(
                    "report_generation_failed",
                    evaluation_id=evaluation_id,
                    report_type=report_type,
                    error=str(e),
                )
                raise

            except Exception as e:
                logger.error(
                    "report_type_failed",
                    evaluation_id=evaluation_id,
                    report_type=report_type,
                    error=str(e),
                )
                # Continue with other report types
                continue

        # Step 6: Update evaluation status to COMPLETE
        evaluation.status = "COMPLETE"
        session.commit()

        # Step 7: Log audit action
        log_audit_action_sync(
            session=session,
            action="report.generated",
            entity_type="evaluation",
            entity_id=evaluation_id,
            organisation_id=str(evaluation.organisation_id),
            after_state={
                "verdict": verdict.verdict,
                "criteria_passed": verdict.criteria_passed,
                "criteria_failed": verdict.criteria_failed,
                "total_findings": verdict.total_findings,
                "reports_generated": reports_generated,
            },
        )
        session.commit()

        logger.info(
            "report_generation_completed",
            task_id=task_id,
            evaluation_id=evaluation_id,
            reports_generated=len(reports_generated),
            verdict=verdict.verdict,
        )

        # Step 8: Register evaluation in longitudinal series (fire-and-forget)
        try:
            snapshot = register_evaluation_in_series_sync(session, UUID(evaluation_id))
            if snapshot:
                session.commit()
                logger.info(
                    "longitudinal_series_registered",
                    evaluation_id=evaluation_id,
                    series_id=str(snapshot.series_id),
                    snapshot_id=str(snapshot.id),
                )
        except Exception as series_error:
            # Series registration failure must NOT fail report generation
            logger.warning(
                "longitudinal_series_registration_failed",
                evaluation_id=evaluation_id,
                error=str(series_error),
            )
            # Rollback any partial series changes but don't propagate
            session.rollback()

        # Publish: Report generation complete event
        publish_task_event(task_id, make_event("complete", {
            "step": "complete",
            "message": "All reports generated successfully",
            "verdict": verdict.verdict,
            "criteria_passed": verdict.criteria_passed,
            "criteria_failed": verdict.criteria_failed,
            "total_findings": verdict.total_findings,
            "reports_generated": reports_generated,
            "evaluation_id": evaluation_id,
        }))

        # Step 9: Return result
        return {
            "evaluation_id": evaluation_id,
            "reports_generated": len(reports_generated),
            "report_types": reports_generated,
            "verdict": verdict.verdict,
            "criteria_failed": verdict.criteria_failed,
            "criteria_passed": verdict.criteria_passed,
            "total_findings": verdict.total_findings,
        }

    except Exception as e:
        logger.error(
            "report_generation_failed",
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

        # Don't reset evaluation status to AUDITING — leave it at REPORTING
        # so user can retry
        session.rollback()
        raise

    finally:
        session.close()


@celery_app.task(name="tasks.report.cleanup_old_reports")
def cleanup_old_reports() -> dict:
    """
    Periodic task to clean up old reports from object storage.

    This helps manage storage costs by removing reports older than
    the configured retention period.
    """
    logger.info("report_cleanup_starting")

    # TODO: Implement cleanup logic based on retention policy
    deleted_count = 0

    logger.info(
        "report_cleanup_completed",
        deleted_count=deleted_count,
    )

    return {"deleted_count": deleted_count}
