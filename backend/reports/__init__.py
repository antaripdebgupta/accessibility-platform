"""
Reports Package.

Contains modules for generating accessibility conformance reports:
- verdict.py: Conformance verdict computation
- generator.py: PDF report generation with WeasyPrint
- earl_export.py: W3C EARL JSON-LD export
- csv_export.py: CSV findings export
"""

from reports.verdict import VerdictResult, FailedCriterion, compute_verdict
from reports.generator import generate_pdf_report, ReportGenerationError
from reports.earl_export import generate_earl
from reports.csv_export import generate_csv

__all__ = [
    "VerdictResult",
    "FailedCriterion",
    "compute_verdict",
    "generate_pdf_report",
    "ReportGenerationError",
    "generate_earl",
    "generate_csv",
]
