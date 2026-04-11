"""
Trend Computation Engine.

Provides data structures and functions for computing accessibility trends
from evaluation series snapshots.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Any

from models.series_snapshot import SeriesSnapshot


@dataclass
class CriterionTrend:
    """
    Trend data for a single WCAG criterion across evaluation snapshots.
    """
    criterion_code: str
    criterion_name: str
    criterion_level: str
    data_points: List[Dict[str, Any]]  # [{date, count, evaluation_id}]
    direction: str  # "improving" | "regressing" | "stable" | "new"
    change: int  # latest count minus previous count (negative = improving)
    first_seen: Optional[str] = None  # ISO date when criterion first appeared
    last_seen: Optional[str] = None  # ISO date of most recent occurrence


@dataclass
class TrendReport:
    """
    Complete trend report for an evaluation series.
    """
    series_id: str
    series_name: str
    target_url: str
    snapshots: List[Dict[str, Any]]  # ordered list of snapshot data
    total_findings_trend: List[Dict[str, Any]]  # [{date, count, evaluation_id}]
    verdict_history: List[Dict[str, Any]]  # [{date, verdict, evaluation_id}]
    criteria_trends: List[CriterionTrend]
    regressing_criteria: List[CriterionTrend] = field(default_factory=list)
    improving_criteria: List[CriterionTrend] = field(default_factory=list)
    new_failures: List[CriterionTrend] = field(default_factory=list)
    resolved_criteria: List[str] = field(default_factory=list)  # criterion codes
    summary: Dict[str, Any] = field(default_factory=dict)


def _format_date(dt: datetime) -> Optional[str]:
    """Format datetime as ISO date string."""
    return dt.isoformat() if dt else None


def _compute_direction(
    latest_count: int,
    previous_count: int,
    had_findings_before_previous: bool,
    num_snapshots: int,
) -> str:
    """
    Compute trend direction for a criterion.

    Args:
        latest_count: Finding count in latest snapshot
        previous_count: Finding count in previous snapshot
        had_findings_before_previous: Whether criterion had findings in any snapshot before the previous one
        num_snapshots: Total number of snapshots

    Returns:
        Direction string: "improving", "regressing", "stable", or "new"
    """
    if num_snapshots < 2:
        return "stable"

    change = latest_count - previous_count

    # Resolved: had findings but now zero
    if latest_count == 0 and previous_count > 0:
        return "improving"

    # New failure: appears in latest, never seen before (not just previous)
    if latest_count > 0 and previous_count == 0 and not had_findings_before_previous:
        return "new"

    # Standard direction
    if change > 0:
        return "regressing"
    elif change < 0:
        return "improving"
    else:
        return "stable"


def compute_trends(
    snapshots: List[SeriesSnapshot],
    wcag_map: Dict[str, Dict[str, str]],
    series_id: str = "",
    series_name: str = "",
    target_url: str = "",
) -> TrendReport:
    """
    Compute comprehensive trend analysis from evaluation snapshots.

    Args:
        snapshots: List of SeriesSnapshot objects (will be sorted by date)
        wcag_map: Mapping of criterion_code to {name, level} dict
        series_id: Series UUID string
        series_name: Human-readable series name
        target_url: Target URL of the series

    Returns:
        TrendReport with all computed trends and analysis
    """
    # Handle empty snapshots
    if not snapshots:
        return TrendReport(
            series_id=series_id,
            series_name=series_name,
            target_url=target_url,
            snapshots=[],
            total_findings_trend=[],
            verdict_history=[],
            criteria_trends=[],
            regressing_criteria=[],
            improving_criteria=[],
            new_failures=[],
            resolved_criteria=[],
            summary={
                "total_evaluations": 0,
                "date_range": {"from": None, "to": None},
                "overall_direction": "stable",
                "net_change": 0,
                "regressions_count": 0,
                "improvements_count": 0,
            },
        )

    # Step 1: Sort snapshots by snapshot_date ascending
    sorted_snapshots = sorted(snapshots, key=lambda s: s.snapshot_date)

    # Step 2: Build snapshot list for response
    snapshot_data = []
    for s in sorted_snapshots:
        snapshot_data.append({
            "id": str(s.id),
            "evaluation_id": str(s.evaluation_id),
            "snapshot_date": _format_date(s.snapshot_date),
            "total_findings": s.total_findings,
            "confirmed_findings": s.confirmed_findings,
            "dismissed_findings": s.dismissed_findings,
            "open_findings": s.open_findings,
            "criteria_failed": s.criteria_failed,
            "criteria_passed": s.criteria_passed,
            "conformance_verdict": s.conformance_verdict,
            "findings_by_severity": s.findings_by_severity,
            "findings_by_criterion": s.findings_by_criterion,
        })

    # Step 3: Build total_findings_trend
    total_findings_trend = [
        {
            "date": _format_date(s.snapshot_date),
            "count": s.confirmed_findings,
            "evaluation_id": str(s.evaluation_id),
        }
        for s in sorted_snapshots
    ]

    # Step 4: Build verdict_history
    verdict_history = [
        {
            "date": _format_date(s.snapshot_date),
            "verdict": s.conformance_verdict,
            "evaluation_id": str(s.evaluation_id),
        }
        for s in sorted_snapshots
    ]

    # Step 5: Build per-criterion trends
    # Collect all criteria codes seen across all snapshots
    all_criteria = set()
    for s in sorted_snapshots:
        if s.findings_by_criterion:
            all_criteria.update(s.findings_by_criterion.keys())

    criteria_trends = []
    regressing_criteria = []
    improving_criteria = []
    new_failures = []
    resolved_criteria = []

    for criterion_code in sorted(all_criteria):
        # Build data points for this criterion
        data_points = []
        first_seen = None
        last_seen = None

        for s in sorted_snapshots:
            count = 0
            if s.findings_by_criterion and criterion_code in s.findings_by_criterion:
                count = s.findings_by_criterion[criterion_code]

            data_points.append({
                "date": _format_date(s.snapshot_date),
                "count": count,
                "evaluation_id": str(s.evaluation_id),
            })

            if count > 0:
                if first_seen is None:
                    first_seen = _format_date(s.snapshot_date)
                last_seen = _format_date(s.snapshot_date)

        # Compute change and direction
        latest_count = data_points[-1]["count"] if data_points else 0
        previous_count = data_points[-2]["count"] if len(data_points) >= 2 else 0

        # Check if criterion had findings in any snapshot before the previous one
        had_findings_before_previous = False
        if len(data_points) >= 3:
            for dp in data_points[:-2]:
                if dp["count"] > 0:
                    had_findings_before_previous = True
                    break

        change = latest_count - previous_count
        direction = _compute_direction(
            latest_count,
            previous_count,
            had_findings_before_previous,
            len(sorted_snapshots),
        )

        # Get criterion metadata from wcag_map
        criterion_info = wcag_map.get(criterion_code, {})
        criterion_name = criterion_info.get("name", "") or criterion_code
        criterion_level = criterion_info.get("level", "") or ""

        trend = CriterionTrend(
            criterion_code=criterion_code,
            criterion_name=criterion_name,
            criterion_level=criterion_level,
            data_points=data_points,
            direction=direction,
            change=change,
            first_seen=first_seen,
            last_seen=last_seen,
        )
        criteria_trends.append(trend)

        # Categorise by direction
        if direction == "regressing":
            regressing_criteria.append(trend)
        elif direction == "improving":
            improving_criteria.append(trend)
            # Check if resolved (was present, now zero)
            if latest_count == 0 and previous_count > 0:
                resolved_criteria.append(criterion_code)
        elif direction == "new":
            new_failures.append(trend)

    # Step 6: Compute summary
    first_snapshot = sorted_snapshots[0]
    last_snapshot = sorted_snapshots[-1]

    first_confirmed = first_snapshot.confirmed_findings
    latest_confirmed = last_snapshot.confirmed_findings
    net_change = latest_confirmed - first_confirmed

    # Determine overall direction
    if net_change < 0:
        overall_direction = "improving"
    elif net_change > 0:
        overall_direction = "regressing"
    else:
        overall_direction = "stable"

    summary = {
        "total_evaluations": len(sorted_snapshots),
        "date_range": {
            "from": _format_date(first_snapshot.snapshot_date),
            "to": _format_date(last_snapshot.snapshot_date),
        },
        "overall_direction": overall_direction,
        "net_change": net_change,
        "regressions_count": len(regressing_criteria) + len(new_failures),
        "improvements_count": len(improving_criteria),
    }

    # Step 7: Build and return TrendReport
    return TrendReport(
        series_id=series_id,
        series_name=series_name,
        target_url=target_url,
        snapshots=snapshot_data,
        total_findings_trend=total_findings_trend,
        verdict_history=verdict_history,
        criteria_trends=criteria_trends,
        regressing_criteria=regressing_criteria,
        improving_criteria=improving_criteria,
        new_failures=new_failures,
        resolved_criteria=resolved_criteria,
        summary=summary,
    )


def filter_trends_by_criterion(
    report: TrendReport,
    criterion_code: str,
) -> TrendReport:
    """
    Filter a trend report to only include a specific criterion.

    Args:
        report: Full TrendReport
        criterion_code: WCAG criterion code to filter by

    Returns:
        TrendReport with only the specified criterion
    """
    matching = [t for t in report.criteria_trends if t.criterion_code == criterion_code]

    return TrendReport(
        series_id=report.series_id,
        series_name=report.series_name,
        target_url=report.target_url,
        snapshots=report.snapshots,
        total_findings_trend=report.total_findings_trend,
        verdict_history=report.verdict_history,
        criteria_trends=matching,
        regressing_criteria=[t for t in matching if t.direction == "regressing"],
        improving_criteria=[t for t in matching if t.direction == "improving"],
        new_failures=[t for t in matching if t.direction == "new"],
        resolved_criteria=[criterion_code] if criterion_code in report.resolved_criteria else [],
        summary=report.summary,
    )


def trend_report_to_dict(report: TrendReport) -> dict:
    """
    Convert TrendReport to a JSON-serializable dictionary.

    Args:
        report: TrendReport instance

    Returns:
        Dictionary representation
    """
    def criterion_trend_to_dict(ct: CriterionTrend) -> dict:
        return {
            "criterion_code": ct.criterion_code,
            "criterion_name": ct.criterion_name,
            "criterion_level": ct.criterion_level,
            "data_points": ct.data_points,
            "direction": ct.direction,
            "change": ct.change,
            "first_seen": ct.first_seen,
            "last_seen": ct.last_seen,
        }

    return {
        "series_id": report.series_id,
        "series_name": report.series_name,
        "target_url": report.target_url,
        "snapshots": report.snapshots,
        "total_findings_trend": report.total_findings_trend,
        "verdict_history": report.verdict_history,
        "criteria_trends": [criterion_trend_to_dict(ct) for ct in report.criteria_trends],
        "regressing_criteria": [criterion_trend_to_dict(ct) for ct in report.regressing_criteria],
        "improving_criteria": [criterion_trend_to_dict(ct) for ct in report.improving_criteria],
        "new_failures": [criterion_trend_to_dict(ct) for ct in report.new_failures],
        "resolved_criteria": report.resolved_criteria,
        "summary": report.summary,
    }
