"""
Scanners Package.

Provides accessibility scanning functionality using axe-core.
"""

from scanners.axe_wcag_map import AXE_WCAG_MAP, IMPACT_SEVERITY_MAP, get_wcag_criterion_ids
from scanners.axe_runner import AxeResult, run_axe_on_page
from scanners.normalise import normalise_axe_results

__all__ = [
    "AXE_WCAG_MAP",
    "IMPACT_SEVERITY_MAP",
    "get_wcag_criterion_ids",
    "AxeResult",
    "run_axe_on_page",
    "normalise_axe_results",
]
