"""
Conformance Verdict Engine.

Computes WCAG conformance verdicts for accessibility evaluations.
Determines whether a website CONFORMS, DOES_NOT_CONFORM, or CANNOT_DETERMINE
based on confirmed findings and scanned pages.
"""

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session

from models.evaluation import EvaluationProject
from models.finding import Finding
from models.page import Page
from models.wcag import WcagCriterion
from profiles.engine import get_all_profiles_summary


@dataclass
class FailedCriterion:
    """
    Represents a WCAG criterion that failed during evaluation.

    Attributes:
        criterion_code: WCAG criterion ID (e.g., "1.1.1")
        criterion_name: Human-readable name (e.g., "Non-text Content")
        criterion_level: Conformance level ("A" or "AA")
        finding_count: Number of findings for this criterion
        findings: List of finding details
    """
    criterion_code: str
    criterion_name: str
    criterion_level: str
    finding_count: int
    findings: list[dict] = field(default_factory=list)


@dataclass
class VerdictResult:
    """
    Result of conformance verdict computation.

    Attributes:
        verdict: Overall verdict (CONFORMS, DOES_NOT_CONFORM, CANNOT_DETERMINE)
        criteria_passed: Number of criteria that passed
        criteria_failed: Number of criteria that failed
        criteria_na: Number of criteria marked as not applicable
        failed_criteria: List of failed criteria with details
        total_findings: Total number of confirmed findings
        confirmed_findings: Count of confirmed findings
        dismissed_findings: Count of dismissed findings
        pages_scanned: Number of pages with completed scans
        evaluation_title: Title of the evaluation project
        target_url: Target website URL
        wcag_version: WCAG version (e.g., "2.1")
        conformance_level: Target conformance level (e.g., "AA")
        generated_at: ISO format timestamp of when verdict was computed
        profile_summaries: Summaries for each disability profile
    """
    verdict: str
    criteria_passed: int
    criteria_failed: int
    criteria_na: int
    failed_criteria: list[FailedCriterion]
    total_findings: int
    confirmed_findings: int
    dismissed_findings: int
    pages_scanned: int
    evaluation_title: str
    target_url: str
    wcag_version: str
    conformance_level: str
    generated_at: str
    profile_summaries: dict[str, dict] = field(default_factory=dict)


def compute_verdict(
    evaluation_id: str,
    db_session: Session,
    conformance_level: str = "AA",
) -> VerdictResult:
    """
    Compute the conformance verdict for an evaluation.

    This is a synchronous function designed to be called from a Celery task.
    It analyzes all confirmed findings and determines whether the evaluated
    website conforms to the specified WCAG conformance level.

    Args:
        evaluation_id: The evaluation UUID as a string
        db_session: SQLAlchemy synchronous session
        conformance_level: Target conformance level ("A", "AA", or "AAA")

    Returns:
        VerdictResult with complete conformance analysis

    Raises:
        ValueError: If evaluation not found
    """
    eval_uuid = UUID(evaluation_id)

    # Step 1: Fetch EvaluationProject
    stmt = select(EvaluationProject).where(EvaluationProject.id == eval_uuid)
    result = db_session.execute(stmt)
    evaluation = result.scalar_one_or_none()

    if evaluation is None:
        raise ValueError(f"Evaluation not found: {evaluation_id}")

    # Use evaluation's conformance level if not explicitly specified
    target_level = conformance_level or evaluation.conformance_level or "AA"

    # Step 2: Fetch all WcagCriterion rows at or below conformance level
    if target_level == "A":
        level_filter = WcagCriterion.level.in_(["A"])
    elif target_level == "AA":
        level_filter = WcagCriterion.level.in_(["A", "AA"])
    else:  # AAA
        level_filter = WcagCriterion.level.in_(["A", "AA", "AAA"])

    criteria_stmt = select(WcagCriterion).where(level_filter)
    criteria_result = db_session.execute(criteria_stmt)
    all_criteria = {c.id: c for c in criteria_result.scalars().all()}

    # Step 3: Fetch ALL confirmed findings for this evaluation
    confirmed_stmt = (
        select(Finding)
        .where(
            and_(
                Finding.evaluation_id == eval_uuid,
                Finding.status == "CONFIRMED",
            )
        )
        .options()  # We'll join manually for page/criterion
    )
    confirmed_result = db_session.execute(confirmed_stmt)
    confirmed_findings_list = list(confirmed_result.scalars().all())

    # Eagerly load page and criterion for each finding
    page_ids = {f.page_id for f in confirmed_findings_list}
    criterion_ids = {f.criterion_id for f in confirmed_findings_list if f.criterion_id}

    # Fetch pages
    pages_map = {}
    if page_ids:
        pages_stmt = select(Page).where(Page.id.in_(page_ids))
        pages_result = db_session.execute(pages_stmt)
        pages_map = {p.id: p for p in pages_result.scalars().all()}

    # Step 4: Count dismissed findings
    dismissed_stmt = select(func.count(Finding.id)).where(
        and_(
            Finding.evaluation_id == eval_uuid,
            Finding.status == "DISMISSED",
        )
    )
    dismissed_result = db_session.execute(dismissed_stmt)
    dismissed_count = dismissed_result.scalar() or 0

    # Step 5: Count scanned pages with COMPLETE status
    scanned_stmt = select(func.count(Page.id)).where(
        and_(
            Page.evaluation_id == eval_uuid,
            Page.scan_status == "COMPLETE",
        )
    )
    scanned_result = db_session.execute(scanned_stmt)
    pages_scanned = scanned_result.scalar() or 0

    # Step 6: Group confirmed findings by criterion_id
    failed_criteria_map: dict[UUID, list[Finding]] = defaultdict(list)
    for finding in confirmed_findings_list:
        if finding.criterion_id:
            failed_criteria_map[finding.criterion_id].append(finding)

    # Step 7: Build failed_criteria list
    failed_criteria: list[FailedCriterion] = []
    for criterion_id, findings in failed_criteria_map.items():
        criterion = all_criteria.get(criterion_id)
        if criterion:
            finding_details = []
            for f in findings:
                page = pages_map.get(f.page_id)
                finding_details.append({
                    "description": f.description,
                    "severity": f.severity or "moderate",
                    "page_url": page.url if page else "",
                    "css_selector": f.css_selector or "",
                })

            failed_criteria.append(FailedCriterion(
                criterion_code=criterion.criterion_id,
                criterion_name=criterion.name,
                criterion_level=criterion.level,
                finding_count=len(findings),
                findings=finding_details,
            ))

    # Sort by criterion_code
    failed_criteria.sort(key=lambda fc: fc.criterion_code)

    # Step 8: Compute counts
    failed_criterion_ids = set(failed_criteria_map.keys())
    # Only count criteria that are in our target level set
    relevant_failed_ids = failed_criterion_ids.intersection(set(all_criteria.keys()))
    criteria_failed = len(relevant_failed_ids)
    criteria_passed = len(all_criteria) - criteria_failed
    criteria_na = 0  # Reserved for future use

    # Step 9: Determine verdict
    if len(confirmed_findings_list) == 0 and pages_scanned == 0:
        verdict = "CANNOT_DETERMINE"
    elif criteria_failed > 0:
        verdict = "DOES_NOT_CONFORM"
    else:
        verdict = "CONFORMS"

    # Step 10: Compute profile summaries for all disability profiles
    # Convert findings to dict format expected by profile engine
    # First, fetch ALL criteria (not just level-filtered) to get criterion codes
    all_criteria_stmt = select(WcagCriterion)
    all_criteria_result = db_session.execute(all_criteria_stmt)
    all_criteria_full = {c.id: c for c in all_criteria_result.scalars().all()}

    findings_for_profiles = []
    for f in confirmed_findings_list:
        # Get criterion code from criterion_id
        criterion = all_criteria_full.get(f.criterion_id) if f.criterion_id else None
        findings_for_profiles.append({
            "id": str(f.id),
            "criterion_code": criterion.criterion_id if criterion else None,  # Use criterion_code, not criterion_id
            "severity": f.severity or "moderate",
            "status": f.status,
        })

    profile_summaries = get_all_profiles_summary(findings_for_profiles)

    # Step 11: Return VerdictResult
    return VerdictResult(
        verdict=verdict,
        criteria_passed=criteria_passed,
        criteria_failed=criteria_failed,
        criteria_na=criteria_na,
        failed_criteria=failed_criteria,
        total_findings=len(confirmed_findings_list),
        confirmed_findings=len(confirmed_findings_list),
        dismissed_findings=dismissed_count,
        pages_scanned=pages_scanned,
        evaluation_title=evaluation.title,
        target_url=evaluation.target_url,
        wcag_version=evaluation.wcag_version or "2.1",
        conformance_level=target_level,
        generated_at=datetime.utcnow().isoformat() + "Z",
        profile_summaries=profile_summaries,
    )
