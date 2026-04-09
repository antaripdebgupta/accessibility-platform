"""
WCAG-EM Sampling Engine.

Core algorithm for structured page sampling following Step 3 of the
W3C Website Accessibility Conformance Evaluation Methodology (WCAG-EM).

This module provides:
- SampleConfig: Configuration options for the sampling algorithm
- SampleResult: Results of the sampling computation
- compute_sample: Main sampling algorithm implementation

WCAG-EM Step 3 requires:
1. Structured Sample: Pages selected deliberately to cover all page types,
   technologies, and key user journeys
2. Random Sample: Pages selected randomly to catch issues not covered by
   deliberate selection (minimum 10% of total or 5 pages)
3. Combined Sample: Deduplicated union of structured + random samples
"""

import hashlib
import random
from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import urlparse


@dataclass
class SampleConfig:
    """Configuration for the sampling algorithm.

    Attributes:
        max_sample_size: Maximum pages in the combined sample (default 15, cap 30)
        min_sample_size: Minimum pages required (default 5, floor 3)
        random_sample_ratio: Percentage of eligible pages for random selection (default 0.1)
        required_page_types: Page types that MUST be included if they exist
        manual_inclusions: Page IDs that are always included regardless of algorithm
        manual_exclusions: Page IDs that are always excluded
        evaluation_id: Used as random seed for reproducible sampling
    """
    max_sample_size: int = 15
    min_sample_size: int = 5
    random_sample_ratio: float = 0.1
    required_page_types: list[str] = field(default_factory=list)
    manual_inclusions: list[str] = field(default_factory=list)
    manual_exclusions: list[str] = field(default_factory=list)
    evaluation_id: Optional[str] = None

    def __post_init__(self) -> None:
        """Validate and normalize configuration values."""
        # Enforce bounds on sample sizes
        # max_sample_size: 5-30 range
        self.max_sample_size = max(5, min(30, self.max_sample_size))

        # min_sample_size: 3 to max_sample_size range (was capped at 10, now follows max)
        self.min_sample_size = max(3, min(self.max_sample_size, self.min_sample_size))

        # Clamp random ratio to 0-30%
        self.random_sample_ratio = max(0.0, min(0.3, self.random_sample_ratio))

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "max_sample_size": self.max_sample_size,
            "min_sample_size": self.min_sample_size,
            "random_sample_ratio": self.random_sample_ratio,
            "required_page_types": self.required_page_types,
            "manual_inclusions": self.manual_inclusions,
            "manual_exclusions": self.manual_exclusions,
        }


@dataclass
class SampleResult:
    """Results of the sampling algorithm.

    Attributes:
        structured_pages: Page IDs selected by structured algorithm
        random_pages: Page IDs selected randomly
        combined_pages: Deduplicated union — final sample (insertion order preserved)
        structured_count: Number of structurally selected pages
        random_count: Number of randomly selected pages
        total_count: Total unique pages in combined sample
        coverage: Page type → count in final sample
        reasoning: Human-readable explanations of each selection
    """
    structured_pages: list[str] = field(default_factory=list)
    random_pages: list[str] = field(default_factory=list)
    combined_pages: list[str] = field(default_factory=list)
    structured_count: int = 0
    random_count: int = 0
    total_count: int = 0
    coverage: dict[str, int] = field(default_factory=dict)
    reasoning: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "structured_pages": self.structured_pages,
            "random_pages": self.random_pages,
            "combined_pages": self.combined_pages,
            "structured_count": self.structured_count,
            "random_count": self.random_count,
            "total_count": self.total_count,
            "coverage": self.coverage,
            "reasoning": self.reasoning,
        }


# Priority order for page type selection in structured sample
# Higher priority types are selected first when building type coverage
PAGE_TYPE_PRIORITY = [
    "form",
    "search",
    "auth",
    "login",
    "navigation",
    "media",
    "contact",
    "product",
    "article",
    "error",
    "other",
]


def _is_home_page(page: dict) -> bool:
    """Check if a page is the homepage.

    A page is considered the homepage if:
    - page_type is "home" or "homepage"
    - URL path is "/" or empty

    Args:
        page: Page dictionary with 'url' and 'page_type' keys

    Returns:
        True if the page is identified as a homepage
    """
    page_type = (page.get("page_type") or "").lower()
    if page_type in ("home", "homepage"):
        return True

    url = page.get("url", "")
    try:
        parsed = urlparse(url)
        path = parsed.path.rstrip("/")
        return path == "" or path == "/"
    except Exception:
        return False


def _get_page_type(page: dict) -> str:
    """Get normalized page type, defaulting to 'other'."""
    return (page.get("page_type") or "other").lower()


def _sort_by_type_priority(pages: list[dict]) -> list[dict]:
    """Sort pages by type priority (higher priority types first)."""
    def priority_key(page: dict) -> int:
        page_type = _get_page_type(page)
        try:
            return PAGE_TYPE_PRIORITY.index(page_type)
        except ValueError:
            # Unknown types get lowest priority
            return len(PAGE_TYPE_PRIORITY)

    return sorted(pages, key=priority_key)


def _truncate_url(url: str, max_length: int = 60) -> str:
    """Truncate URL for human-readable reasoning."""
    if len(url) <= max_length:
        return url
    return url[:max_length - 3] + "..."


def compute_sample(pages: list[dict], config: dict | SampleConfig) -> SampleResult:
    """
    Compute page sample following WCAG-EM Step 3 methodology.

    This algorithm implements the W3C Website Accessibility Conformance
    Evaluation Methodology structured sampling approach:

    1. Structured Sample: Deliberate selection for coverage
       - Always includes homepage
       - Includes required page types
       - Ensures diversity across all page types

    2. Random Sample: Complement to catch missed issues
       - Minimum 10% of eligible pages or enough to reach min_sample_size

    3. Combined Sample: Deduplicated union, capped at max_sample_size

    Args:
        pages: List of page dictionaries with keys:
            - id: Page UUID string
            - url: Full URL
            - title: Page title (optional)
            - page_type: Classification string (optional)
            - http_status: HTTP response code (optional)
        config: SampleConfig instance or dict with configuration options

    Returns:
        SampleResult with selected pages, counts, coverage, and reasoning

    Example:
        >>> pages = [
        ...     {"id": "1", "url": "https://example.com/", "page_type": "home"},
        ...     {"id": "2", "url": "https://example.com/contact", "page_type": "form"},
        ... ]
        >>> config = {"max_sample_size": 15, "min_sample_size": 5}
        >>> result = compute_sample(pages, config)
        >>> result.total_count
        2
    """
    # Convert dict config to SampleConfig
    if isinstance(config, dict):
        config = SampleConfig(**config)

    result = SampleResult()
    structured_set: set[str] = set()
    reasoning: list[str] = []

    # Step 1: Filter eligible pages
    eligible_pages: list[dict] = []
    excluded_count = 0
    error_count = 0

    for page in pages:
        page_id = str(page.get("id", ""))

        # Skip pages in manual exclusions
        if page_id in config.manual_exclusions:
            excluded_count += 1
            reasoning.append(
                f"Excluded {_truncate_url(page.get('url', 'unknown'))} "
                f"(manually excluded from sample)"
            )
            continue

        # Skip pages with actual HTTP errors (4xx, 5xx)
        # IMPORTANT: http_status=0 means "unknown/not fetched" - NOT an error
        # Only exclude pages that actually returned error status codes
        http_status = page.get("http_status") or 0
        if http_status >= 400 and http_status != 0:
            error_count += 1
            continue

        # Include all other pages - don't filter by page_type
        eligible_pages.append(page)

    if error_count > 0:
        reasoning.append(
            f"Excluded {error_count} page(s) with HTTP error status (4xx/5xx)"
        )

    # Handle edge case: no eligible pages at all
    if not eligible_pages:
        reasoning.append(
            "No eligible pages found. All pages were either manually excluded "
            "or returned HTTP error status codes."
        )
        return result

    # Special case: fewer pages than minimum sample size - include all
    if len(eligible_pages) <= config.min_sample_size:
        reasoning.append(
            f"Only {len(eligible_pages)} eligible page(s) found — "
            f"all included to meet minimum sample requirement. "
            f"Consider crawling more pages before sampling."
        )
        # Include all eligible pages directly
        all_ids = [str(p.get("id", "")) for p in eligible_pages]
        coverage: dict[str, int] = {}
        for page in eligible_pages:
            page_type = _get_page_type(page)
            coverage[page_type] = coverage.get(page_type, 0) + 1

        result.structured_pages = all_ids
        result.random_pages = []
        result.combined_pages = all_ids
        result.structured_count = len(all_ids)
        result.random_count = 0
        result.total_count = len(all_ids)
        result.coverage = coverage
        result.reasoning = reasoning
        return result

    # Build lookup for quick access
    page_lookup = {str(p.get("id", "")): p for p in eligible_pages}

    # Step 2: Mandatory inclusions

    # 2a. Always include homepage (unless manually excluded)
    home_page = None
    for page in eligible_pages:
        if _is_home_page(page):
            home_page = page
            break

    if home_page:
        page_id = str(home_page.get("id", ""))
        structured_set.add(page_id)
        reasoning.append(
            f"Added {_truncate_url(home_page.get('url', ''))} as homepage "
            f"(mandatory for WCAG-EM compliance)"
        )

    # 2b. Add manual inclusions
    for manual_id in config.manual_inclusions:
        if manual_id in page_lookup and manual_id not in structured_set:
            page = page_lookup[manual_id]
            structured_set.add(manual_id)
            reasoning.append(
                f"Added {_truncate_url(page.get('url', ''))} "
                f"(manually included in sample)"
            )

    # 2c. Add required page types
    types_covered: set[str] = set()
    for page_id in structured_set:
        if page_id in page_lookup:
            types_covered.add(_get_page_type(page_lookup[page_id]))

    for required_type in config.required_page_types:
        required_type_lower = required_type.lower()
        if required_type_lower in types_covered:
            continue

        # Find first page of this type
        for page in eligible_pages:
            if _get_page_type(page) == required_type_lower:
                page_id = str(page.get("id", ""))
                if page_id not in structured_set:
                    structured_set.add(page_id)
                    types_covered.add(required_type_lower)
                    reasoning.append(
                        f"Added {_truncate_url(page.get('url', ''))} ({required_type}) "
                        f"as required page type"
                    )
                    break

    # Step 3: Structured diversity selection
    structured_target = int(config.max_sample_size * 0.6)

    # Group pages by type
    pages_by_type: dict[str, list[dict]] = {}
    for page in eligible_pages:
        page_type = _get_page_type(page)
        if page_type not in pages_by_type:
            pages_by_type[page_type] = []
        pages_by_type[page_type].append(page)

    # Sort page types by priority
    sorted_types = sorted(
        pages_by_type.keys(),
        key=lambda t: PAGE_TYPE_PRIORITY.index(t) if t in PAGE_TYPE_PRIORITY else len(PAGE_TYPE_PRIORITY)
    )

    # Add one page per type for coverage
    for page_type in sorted_types:
        if len(structured_set) >= structured_target:
            break

        if page_type in types_covered:
            continue

        type_pages = pages_by_type[page_type]
        if type_pages:
            page = type_pages[0]
            page_id = str(page.get("id", ""))
            if page_id not in structured_set:
                structured_set.add(page_id)
                types_covered.add(page_type)
                reasoning.append(
                    f"Added {_truncate_url(page.get('url', ''))} ({page_type}) "
                    f"to ensure page type coverage"
                )

    # Step 4: Random sample
    remaining_pages = [
        p for p in eligible_pages
        if str(p.get("id", "")) not in structured_set
    ]

    # Calculate random target
    # Minimum: 10% of eligible pages OR enough to reach min_sample_size
    random_from_ratio = max(1, int(len(eligible_pages) * config.random_sample_ratio + 0.5))
    random_for_min = max(0, config.min_sample_size - len(structured_set))
    random_target = max(random_from_ratio, random_for_min)

    # Cap to not exceed max_sample_size
    max_random = config.max_sample_size - len(structured_set)
    random_target = min(random_target, max_random)
    random_target = max(0, min(random_target, len(remaining_pages)))

    # Create local Random instance for thread-safety (CRITICAL FIX #1)
    # Use hashlib for deterministic seeding across Python versions (CRITICAL FIX #2)
    if config.evaluation_id:
        # Use SHA-256 hash for consistent, reproducible seeding
        hash_bytes = hashlib.sha256(config.evaluation_id.encode('utf-8')).hexdigest()
        seed = int(hash_bytes[:8], 16)  # Use first 8 hex chars (32 bits)
    else:
        seed = 42  # Fallback deterministic seed

    # Use local Random instance instead of global state (thread-safe)
    rng = random.Random(seed)
    shuffled_remaining = remaining_pages.copy()
    rng.shuffle(shuffled_remaining)

    random_pages: list[str] = []
    for i, page in enumerate(shuffled_remaining):
        if i >= random_target:
            break
        page_id = str(page.get("id", ""))
        random_pages.append(page_id)

    if random_pages:
        reasoning.append(
            f"Randomly selected {len(random_pages)} page(s) from "
            f"{len(remaining_pages)} remaining eligible pages"
        )

    # Step 5: Combine and cap
    combined: list[str] = list(structured_set) + random_pages

    # Deduplicate while preserving order
    seen: set[str] = set()
    combined_dedup: list[str] = []
    for page_id in combined:
        if page_id not in seen:
            seen.add(page_id)
            combined_dedup.append(page_id)

    # Cap at max_sample_size
    if len(combined_dedup) > config.max_sample_size:
        # Trim from random sample end
        over_count = len(combined_dedup) - config.max_sample_size
        combined_dedup = combined_dedup[:config.max_sample_size]
        reasoning.append(
            f"Capped sample at {config.max_sample_size} pages "
            f"(removed {over_count} from random selection)"
        )

    # Ensure minimum sample size
    if len(combined_dedup) < config.min_sample_size:
        # Add more pages from remaining eligible
        additional_needed = config.min_sample_size - len(combined_dedup)
        remaining_for_min = [
            p for p in eligible_pages
            if str(p.get("id", "")) not in seen
        ]

        for page in remaining_for_min[:additional_needed]:
            page_id = str(page.get("id", ""))
            combined_dedup.append(page_id)
            seen.add(page_id)
            reasoning.append(
                f"Added {_truncate_url(page.get('url', ''))} to meet "
                f"minimum sample size of {config.min_sample_size}"
            )

    # Edge case: if combined sample is still empty but eligible pages exist,
    # force-include the first eligible page (should never happen, but safety check)
    if not combined_dedup and eligible_pages:
        first_page = eligible_pages[0]
        page_id = str(first_page.get("id", ""))
        combined_dedup.append(page_id)
        structured_set.add(page_id)
        reasoning.append(
            f"Force-included {_truncate_url(first_page.get('url', ''))} "
            f"to ensure at least one page in sample"
        )

    # Step 6: Build coverage map
    coverage: dict[str, int] = {}
    for page_id in combined_dedup:
        if page_id in page_lookup:
            page_type = _get_page_type(page_lookup[page_id])
            coverage[page_type] = coverage.get(page_type, 0) + 1

    # Build result (CRITICAL FIX #3: Count only pages in final sample)
    # Calculate counts from actual final sample, not from intermediate sets
    final_combined_set = set(combined_dedup)
    random_set = set(random_pages)

    # Structured pages that made it to final sample
    final_structured = [p for p in combined_dedup if p in structured_set]
    # Random pages that made it to final sample (excluding those also in structured)
    final_random = [p for p in combined_dedup if p in random_set and p not in structured_set]

    result.structured_pages = final_structured
    result.random_pages = final_random
    result.combined_pages = combined_dedup
    result.structured_count = len(final_structured)
    result.random_count = len(final_random)
    result.total_count = len(combined_dedup)
    result.coverage = coverage
    result.reasoning = reasoning

    return result
