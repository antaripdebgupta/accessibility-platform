"""
WCAG-EM Sampling Module.

Implements Step 3 of the W3C Website Accessibility Conformance Evaluation Methodology.
Provides structured and random page sampling algorithms following WCAG-EM guidelines.

Key components:
- engine.py: Core sampling algorithm with SampleResult dataclass
- service.py: Database integration and sample management
"""

from sampling.engine import compute_sample, SampleResult, SampleConfig

__all__ = [
    "compute_sample",
    "SampleResult",
    "SampleConfig",
]
