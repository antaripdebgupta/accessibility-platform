"""
axe-core WCAG Mapping Module.

Maps axe-core rule IDs to WCAG 2.1 success criterion IDs.
This mapping is used to link automated scan findings to specific WCAG criteria.
"""

# Mapping of axe-core rule IDs to WCAG criterion IDs
# Each rule may map to one or more WCAG criteria
AXE_WCAG_MAP: dict[str, list[str]] = {
    # 1.1 Text Alternatives
    "image-alt": ["1.1.1"],
    "input-image-alt": ["1.1.1"],
    "area-alt": ["1.1.1"],
    "object-alt": ["1.1.1"],
    "svg-img-alt": ["1.1.1"],
    "role-img-alt": ["1.1.1"],

    # 1.2 Time-based Media
    "audio-caption": ["1.2.1", "1.2.2"],
    "video-caption": ["1.2.2"],
    "video-description": ["1.2.3", "1.2.5"],

    # 1.3 Adaptable
    "heading-order": ["1.3.1"],
    "label": ["1.3.1", "4.1.2"],
    "aria-required-children": ["1.3.1", "4.1.2"],
    "aria-required-parent": ["1.3.1", "4.1.2"],
    "table-fake-caption": ["1.3.1"],
    "td-headers-attr": ["1.3.1"],
    "th-has-data-cells": ["1.3.1"],
    "logical-tab-order": ["1.3.2"],
    "css-orientation-lock": ["1.3.4"],
    "autocomplete-valid": ["1.3.5"],

    # 1.4 Distinguishable
    "color-contrast": ["1.4.3"],
    "color-contrast-enhanced": ["1.4.6"],
    "meta-viewport": ["1.4.4"],
    "meta-viewport-large": ["1.4.4"],
    "text-spacing": ["1.4.12"],
    "target-size": ["2.5.5"],

    # 2.1 Keyboard Accessible
    "keyboard": ["2.1.1"],
    "focusable-disabled": ["2.1.1"],
    "scrollable-region-focusable": ["2.1.1"],
    "focus-trap": ["2.1.2"],
    "no-positive-tabindex": ["2.4.3"],

    # 2.2 Enough Time
    "meta-refresh": ["2.2.1"],
    "meta-refresh-no-exceptions": ["2.2.1"],
    "blink": ["2.2.2"],
    "marquee": ["2.2.2"],

    # 2.3 Seizures and Physical Reactions
    # No common axe rules for this category

    # 2.4 Navigable
    "bypass": ["2.4.1"],
    "skip-link": ["2.4.1"],
    "frame-title": ["2.4.1", "4.1.2"],
    "document-title": ["2.4.2"],
    "focus-order-semantics": ["2.4.3"],
    "link-name": ["2.4.4", "4.1.2"],
    "link-in-text-block": ["1.4.1"],
    "identical-links-same-purpose": ["2.4.9"],

    # 2.5 Input Modalities
    "label-content-name-mismatch": ["2.5.3"],

    # 3.1 Readable
    "html-has-lang": ["3.1.1"],
    "html-lang-valid": ["3.1.1"],
    "html-xml-lang-mismatch": ["3.1.1"],
    "valid-lang": ["3.1.2"],

    # 3.2 Predictable
    "select-name": ["3.2.2"],

    # 3.3 Input Assistance
    "form-field-multiple-labels": ["3.3.2"],

    # 4.1 Compatible
    "duplicate-id-active": ["4.1.1"],
    "duplicate-id-aria": ["4.1.1"],
    "duplicate-id": ["4.1.1"],
    "button-name": ["4.1.2"],
    "aria-required-attr": ["4.1.2"],
    "aria-roles": ["4.1.2"],
    "aria-valid-attr": ["4.1.2"],
    "aria-valid-attr-value": ["4.1.2"],
    "aria-allowed-attr": ["4.1.2"],
    "aria-hidden-body": ["4.1.2"],
    "aria-hidden-focus": ["4.1.2"],
    "aria-input-field-name": ["4.1.2"],
    "aria-toggle-field-name": ["4.1.2"],
    "aria-tooltip-name": ["4.1.2"],
    "aria-treeitem-name": ["4.1.2"],
    "aria-command-name": ["4.1.2"],
    "aria-meter-name": ["4.1.2"],
    "aria-progressbar-name": ["4.1.2"],
    "nested-interactive": ["4.1.2"],
    "presentation-role-conflict": ["4.1.2"],
    "scope-attr-valid": ["4.1.2"],
    "tabindex": ["4.1.2"],
}

# Mapping of axe-core impact levels to internal severity levels
IMPACT_SEVERITY_MAP: dict[str, str] = {
    "critical": "critical",
    "serious": "serious",
    "moderate": "moderate",
    "minor": "minor",
}


def get_wcag_criterion_ids(rule_id: str) -> list[str]:
    """
    Get WCAG criterion IDs for an axe-core rule.

    Args:
        rule_id: The axe-core rule identifier (e.g., "image-alt")

    Returns:
        List of WCAG criterion ID strings (e.g., ["1.1.1"]).
        Returns empty list if rule is not mapped.
    """
    return AXE_WCAG_MAP.get(rule_id, [])
