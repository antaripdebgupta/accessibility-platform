"""
Longitudinal Analysis Package.

Provides services for tracking and comparing evaluations over time:
- Series management: Group evaluations by target URL
- Snapshot creation: Capture point-in-time metrics
- Trend computation: Analyze changes and detect regressions
"""

from longitudinal.series import (
    get_or_create_series,
    register_evaluation_in_series,
    update_snapshot,
    normalise_url,
)
from longitudinal.trends import (
    CriterionTrend,
    TrendReport,
    compute_trends,
)

__all__ = [
    "get_or_create_series",
    "register_evaluation_in_series",
    "update_snapshot",
    "normalise_url",
    "CriterionTrend",
    "TrendReport",
    "compute_trends",
]
