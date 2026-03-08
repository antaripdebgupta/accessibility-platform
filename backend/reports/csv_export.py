"""
CSV Export Module.

Generates CSV exports of accessibility findings with UTF-8 BOM
for Excel compatibility.
"""

import csv
import io
from typing import Any


def generate_csv(confirmed_findings: list) -> bytes:
    """
    Generate a CSV export of confirmed findings.

    Creates a CSV file with all finding details suitable for import
    into spreadsheet applications or other analysis tools.

    Args:
        confirmed_findings: List of Finding objects with related page/criterion loaded

    Returns:
        bytes: UTF-8 encoded CSV with BOM prefix for Excel compatibility
    """
    # Define column headers
    headers = [
        "finding_id",
        "page_url",
        "wcag_criterion",
        "criterion_name",
        "criterion_level",
        "severity",
        "source",
        "rule_id",
        "description",
        "css_selector",
        "status",
        "reviewer_note",
        "created_at",
    ]

    # Create string buffer
    output = io.StringIO()

    # Add UTF-8 BOM for Excel compatibility
    output.write('\ufeff')

    # Create CSV writer
    writer = csv.writer(output, quoting=csv.QUOTE_ALL)

    # Write header row
    writer.writerow(headers)

    # Write finding rows
    for finding in confirmed_findings:
        # Extract page URL
        page_url = ""
        if hasattr(finding, 'page') and finding.page:
            page_url = finding.page.url
        elif hasattr(finding, 'page_url'):
            page_url = finding.page_url

        # Extract criterion details
        criterion_code = ""
        criterion_name = ""
        criterion_level = ""
        if hasattr(finding, 'criterion') and finding.criterion:
            criterion_code = finding.criterion.criterion_id
            criterion_name = finding.criterion.name
            criterion_level = finding.criterion.level
        elif hasattr(finding, 'criterion_code'):
            criterion_code = getattr(finding, 'criterion_code', '')
            criterion_name = getattr(finding, 'criterion_name', '')
            criterion_level = getattr(finding, 'criterion_level', '')

        # Extract created_at
        created_at = ""
        if hasattr(finding, 'created_at') and finding.created_at:
            created_at = finding.created_at.isoformat()

        # Build row
        row = [
            str(finding.id) if hasattr(finding, 'id') else "",
            page_url,
            criterion_code,
            criterion_name,
            criterion_level,
            getattr(finding, 'severity', '') or "",
            getattr(finding, 'source', '') or "",
            getattr(finding, 'rule_id', '') or "",
            getattr(finding, 'description', '') or "",
            getattr(finding, 'css_selector', '') or "",
            getattr(finding, 'status', '') or "",
            getattr(finding, 'reviewer_note', '') or "",
            created_at,
        ]

        writer.writerow(row)

    # Get string content and encode to bytes
    csv_content = output.getvalue()
    output.close()

    return csv_content.encode('utf-8')
