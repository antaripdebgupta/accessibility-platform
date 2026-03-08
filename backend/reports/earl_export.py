"""
EARL JSON-LD Export Module.

Generates W3C EARL (Evaluation and Report Language) 1.0 compliant
JSON-LD output for accessibility evaluation results.

EARL is the standard format for sharing accessibility test results
and is recognized by W3C and accessibility tool vendors.
"""

from typing import Any, Optional
from datetime import datetime

from reports.verdict import VerdictResult


def generate_earl(
    evaluation: Any,
    confirmed_findings: list,
    verdict: VerdictResult,
) -> dict:
    """
    Generate W3C EARL 1.0 JSON-LD export.

    Creates a structured JSON-LD document conforming to the EARL vocabulary
    that can be consumed by other accessibility tools and reporting systems.

    Args:
        evaluation: The EvaluationProject ORM object
        confirmed_findings: List of confirmed Finding objects with page/criterion loaded
        verdict: The computed VerdictResult

    Returns:
        dict: JSON-LD structure conforming to EARL 1.0
    """
    # Build the @graph array
    graph = []

    # TestSubject — the website being evaluated
    test_subject = {
        "@type": "earl:TestSubject",
        "@id": evaluation.target_url,
        "dcterms:title": evaluation.title,
        "dcterms:description": f"WCAG {evaluation.wcag_version} Level {evaluation.conformance_level} evaluation",
    }
    graph.append(test_subject)

    # Assertor — the tool that performed the evaluation
    assertor = {
        "@type": "earl:Assertor",
        "@id": "https://github.com/accessibility-platform",
        "dcterms:title": "AccessHub Platform",
        "dcterms:description": "WCAG Accessibility Evaluation Platform",
        "schema:version": "0.1.0",
    }
    graph.append(assertor)

    # Overall conformance assertion
    overall_outcome = {
        "CONFORMS": "earl:passed",
        "DOES_NOT_CONFORM": "earl:failed",
        "CANNOT_DETERMINE": "earl:cantTell",
    }.get(verdict.verdict, "earl:cantTell")

    overall_assertion = {
        "@type": "earl:Assertion",
        "earl:assertedBy": {"@id": "https://github.com/accessibility-platform"},
        "earl:subject": {"@id": evaluation.target_url},
        "earl:test": {
            "@id": f"WCAG{evaluation.wcag_version.replace('.', '')}-Level{evaluation.conformance_level}",
            "dcterms:title": f"WCAG {evaluation.wcag_version} Level {evaluation.conformance_level} Conformance",
        },
        "earl:result": {
            "@type": "earl:TestResult",
            "earl:outcome": {"@id": overall_outcome},
            "dcterms:description": f"Overall conformance evaluation: {verdict.verdict}",
            "earl:info": f"{verdict.criteria_passed} criteria passed, {verdict.criteria_failed} criteria failed",
        },
        "earl:mode": {"@id": "earl:automatic"},
        "dcterms:date": verdict.generated_at,
    }
    graph.append(overall_assertion)

    # One earl:Assertion per confirmed finding
    for finding in confirmed_findings:
        # Get page URL
        page_url = ""
        if hasattr(finding, 'page') and finding.page:
            page_url = finding.page.url
        elif hasattr(finding, 'page_url'):
            page_url = finding.page_url

        # Get criterion details
        criterion_code = ""
        criterion_name = ""
        if hasattr(finding, 'criterion') and finding.criterion:
            criterion_code = finding.criterion.criterion_id
            criterion_name = finding.criterion.name
        elif hasattr(finding, 'criterion_code'):
            criterion_code = finding.criterion_code
            criterion_name = getattr(finding, 'criterion_name', '')

        # Build test ID
        if criterion_code:
            test_id = f"WCAG{evaluation.wcag_version.replace('.', '')}-{criterion_code.replace('.', '')}"
            test_title = criterion_name or criterion_code
        else:
            test_id = f"rule:{finding.rule_id}" if finding.rule_id else "rule:unknown"
            test_title = finding.rule_id or "Unknown Rule"

        # Get source for mode
        source = getattr(finding, 'source', 'axe-core')
        mode = "earl:automatic" if source in ("axe-core", "pa11y") else "earl:manual"

        # Get created_at
        created_at = None
        if hasattr(finding, 'created_at') and finding.created_at:
            if isinstance(finding.created_at, datetime):
                created_at = finding.created_at.isoformat()
            else:
                created_at = str(finding.created_at)

        # Build assertion
        assertion = {
            "@type": "earl:Assertion",
            "earl:assertedBy": {"@id": "https://github.com/accessibility-platform"},
            "earl:subject": {"@id": page_url},
            "earl:test": {
                "@id": test_id,
                "dcterms:title": test_title,
            },
            "earl:result": {
                "@type": "earl:TestResult",
                "earl:outcome": {"@id": "earl:failed"},
                "dcterms:description": finding.description,
                "earl:severity": finding.severity or "moderate",
            },
            "earl:mode": {"@id": mode},
        }

        # Add optional fields
        if created_at:
            assertion["dcterms:date"] = created_at

        # Add pointer if CSS selector available
        css_selector = getattr(finding, 'css_selector', None)
        if css_selector:
            assertion["earl:result"]["earl:pointer"] = {
                "@type": "earl:CSSSelector",
                "earl:value": css_selector,
            }

        graph.append(assertion)

    # Build final JSON-LD document
    earl_document = {
        "@context": [
            "http://www.w3.org/ns/earl#",
            "http://www.w3.org/ns/dqv#",
            {
                "schema": "http://schema.org/",
                "dcterms": "http://purl.org/dc/terms/",
            }
        ],
        "@graph": graph,
    }

    return earl_document
