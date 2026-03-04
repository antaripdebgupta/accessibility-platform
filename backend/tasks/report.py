"""
Report Generation Tasks

Tasks for generating PDF accessibility reports.
"""

from tasks import celery_app
from core.logging import get_logger

logger = get_logger(__name__)


@celery_app.task(bind=True, name="tasks.report.generate_pdf_report")
def generate_pdf_report(self, evaluation_id: str):
    """
    Generate a PDF report for an evaluation.

    Args:
        evaluation_id: The evaluation to generate a report for

    Returns:
        URL to the generated PDF in object storage
    """
    logger.info(
        "report_generation_starting",
        evaluation_id=evaluation_id,
    )

    # TODO: Implement PDF generation with WeasyPrint + Jinja2
    # This is a placeholder for Day 1

    report_url = f"/api/v1/evaluations/{evaluation_id}/report.pdf"

    logger.info(
        "report_generation_completed",
        evaluation_id=evaluation_id,
        report_url=report_url,
    )

    return {
        "evaluation_id": evaluation_id,
        "report_url": report_url,
        "status": "completed",
    }


@celery_app.task(name="tasks.report.cleanup_old_reports")
def cleanup_old_reports():
    """
    Periodic task to clean up old reports from object storage.

    This helps manage storage costs by removing reports older than
    the configured retention period.
    """
    logger.info("cleanup_starting")

    # TODO: Implement cleanup logic
    # This is a placeholder for Day 1

    deleted_count = 0

    logger.info(
        "cleanup_completed",
        deleted_count=deleted_count,
    )

    return {"deleted_count": deleted_count}
