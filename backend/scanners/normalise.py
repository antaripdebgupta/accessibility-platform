"""
Finding Normalizer Module.

Normalizes axe-core scan results into the Finding model format.
Handles WCAG criterion mapping, deduplication, and data transformation.
"""

from typing import Optional

from scanners.axe_wcag_map import get_wcag_criterion_ids, IMPACT_SEVERITY_MAP
from scanners.axe_runner import AxeResult
from core.logging import get_logger

logger = get_logger(__name__)


def normalise_axe_results(
    axe_result: AxeResult,
    evaluation_id: str,
    page_id: str,
    wcag_criteria_map: dict[str, str],
) -> list[dict]:
    """
    Normalize axe-core results into finding dictionaries.

    Transforms axe-core violation data into a standardized format
    suitable for database insertion.

    Args:
        axe_result: The AxeResult from axe-core scan
        evaluation_id: The evaluation UUID string
        page_id: The page UUID string
        wcag_criteria_map: Dict mapping criterion_id strings to UUIDs
            (e.g., {"1.1.1": "uuid-here", "1.4.3": "uuid-here"})

    Returns:
        List of finding dictionaries ready for database insertion.
        Deduplicated by (rule_id, css_selector, page_id).
    """
    findings: list[dict] = []
    seen_keys: set[tuple] = set()

    for violation in axe_result.violations:
        rule_id = violation.get("id", "")
        description = violation.get("description", violation.get("help", ""))
        remediation = violation.get("helpUrl", "")
        impact = violation.get("impact", "")
        tags = violation.get("tags", [])

        # Get WCAG criterion IDs for this rule
        criterion_ids = get_wcag_criterion_ids(rule_id)

        # Get the first criterion UUID if available
        criterion_uuid: Optional[str] = None
        if criterion_ids:
            criterion_uuid = wcag_criteria_map.get(criterion_ids[0])

        # Map impact to severity
        severity = IMPACT_SEVERITY_MAP.get(impact, "minor")

        # Process each affected node
        nodes = violation.get("nodes", [])
        for node in nodes:
            # Extract CSS selector
            target = node.get("target", [])
            css_selector = target[0] if target else ""

            # Truncate HTML snippet to 2000 chars
            html_snippet = node.get("html", "")[:2000]

            # Deduplication key
            dedup_key = (rule_id, css_selector, page_id)
            if dedup_key in seen_keys:
                continue
            seen_keys.add(dedup_key)

            # Build finding dictionary
            finding = {
                "evaluation_id": evaluation_id,
                "page_id": page_id,
                "criterion_id": criterion_uuid,
                "source": "axe-core",
                "rule_id": rule_id,
                "description": description,
                "severity": severity,
                "css_selector": css_selector,
                "html_snippet": html_snippet,
                "impact": impact,
                "remediation": remediation,
                "status": "OPEN",
                "raw_result": {
                    "violation_id": rule_id,
                    "tags": tags,
                    "node_html": node.get("html", ""),
                    "failure_summary": node.get("failureSummary", ""),
                },
                "screenshot_key": axe_result.screenshot_key,
            }

            findings.append(finding)

    logger.info(
        "axe_results_normalised",
        page_id=page_id,
        violations_count=len(axe_result.violations),
        findings_count=len(findings),
    )

    return findings
