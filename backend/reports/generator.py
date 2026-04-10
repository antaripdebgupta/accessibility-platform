"""
PDF Report Generator.

Generates PDF accessibility conformance reports using Jinja2 templates
and WeasyPrint for PDF rendering.
"""

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader
from markupsafe import escape

from profiles.definitions import list_profiles
from reports.verdict import VerdictResult


class ReportGenerationError(Exception):
    """Exception raised when report generation fails."""

    def __init__(self, message: str, original_error: Exception | None = None):
        self.message = message
        self.original_error = original_error
        super().__init__(self.message)


def escape_finding_content(finding: dict) -> dict:
    """
    HTML-escape user-provided content in a finding to prevent WeasyPrint crashes.

    Args:
        finding: A finding dictionary

    Returns:
        The finding with escaped content
    """
    escaped = dict(finding)
    fields_to_escape = ['description', 'css_selector', 'html_snippet', 'reviewer_note']

    for field in fields_to_escape:
        if field in escaped and escaped[field]:
            escaped[field] = str(escape(str(escaped[field])))

    return escaped


def generate_pdf_report(
    verdict: VerdictResult,
    evaluation: Any,
    confirmed_findings: list,
) -> bytes:
    """
    Generate a PDF accessibility conformance report.

    Uses Jinja2 templates and WeasyPrint to produce a professionally
    formatted PDF report suitable for client delivery.

    Args:
        verdict: The computed VerdictResult with conformance analysis
        evaluation: The EvaluationProject ORM object
        confirmed_findings: List of confirmed findings (for reference)

    Returns:
        bytes: The generated PDF as bytes

    Raises:
        ReportGenerationError: If PDF generation fails
    """
    try:
        # Import WeasyPrint here to avoid import errors if not installed
        import weasyprint

        # Set up paths
        templates_dir = Path(__file__).parent / "templates"

        # Set up Jinja2 environment
        env = Environment(
            loader=FileSystemLoader(str(templates_dir)),
            autoescape=True,
        )

        # Load CSS content
        css_path = templates_dir / "report_styles.css"
        with open(css_path, 'r', encoding='utf-8') as f:
            css_content = f.read()

        # Load template
        template = env.get_template("report_full.html")

        # Build verdict labels and descriptions
        verdict_labels = {
            "CONFORMS": "✓ Conforms to WCAG",
            "DOES_NOT_CONFORM": "✗ Does Not Conform to WCAG",
            "CANNOT_DETERMINE": "? Cannot Determine Conformance",
        }

        verdict_descriptions = {
            "CONFORMS": f"This website meets WCAG {evaluation.wcag_version} Level {evaluation.conformance_level} requirements based on the pages evaluated.",
            "DOES_NOT_CONFORM": f"This website does not meet WCAG {evaluation.wcag_version} Level {evaluation.conformance_level} requirements. {verdict.criteria_failed} criterion/criteria failed.",
            "CANNOT_DETERMINE": "Insufficient data to determine conformance. Ensure pages have been scanned and findings reviewed.",
        }

        # Escape user-provided content in confirmed findings to prevent WeasyPrint crashes
        escaped_findings = [escape_finding_content(f) if isinstance(f, dict) else f for f in confirmed_findings]

        # Get profile metadata for display
        profiles_metadata = {p.id: {"name": p.name} for p in list_profiles()}

        # Build template context
        context = {
            "verdict": verdict,
            "report_title": f"Accessibility Report — {escape(str(evaluation.title))}",
            "evaluation": evaluation,
            "verdict_label": verdict_labels.get(verdict.verdict, "Unknown"),
            "verdict_description": verdict_descriptions.get(verdict.verdict, ""),
            "css_content": css_content,
            "confirmed_findings": escaped_findings,
            "has_failed_criteria": bool(verdict.failed_criteria) if hasattr(verdict, 'failed_criteria') else False,
            "profile_summaries": verdict.profile_summaries if hasattr(verdict, 'profile_summaries') else {},
            "profiles_metadata": profiles_metadata,
        }

        # Render HTML
        html_string = template.render(**context)

        # Generate PDF with WeasyPrint
        pdf_bytes = weasyprint.HTML(
            string=html_string,
            base_url=str(templates_dir),
        ).write_pdf()

        if pdf_bytes is None:
            raise ReportGenerationError(
                message="WeasyPrint returned empty PDF",
            )

        return pdf_bytes

    except ImportError as e:
        raise ReportGenerationError(
            message="WeasyPrint is not installed. Install with: pip install weasyprint",
            original_error=e,
        )
    except Exception as e:
        raise ReportGenerationError(
            message=f"Failed to generate PDF report: {str(e)}",
            original_error=e,
        )
