#!/usr/bin/env python3
"""
Seed script for WCAG 2.1 Level A and AA Success Criteria.

Inserts all 50 WCAG 2.1 A and AA success criteria into the wcag_criteria table.
Uses INSERT ... ON CONFLICT DO NOTHING to be safe for repeated runs.

Usage:
    python -m scripts.seed_wcag

Or run directly:
    python scripts/seed_wcag.py
"""

import asyncio
import sys
from pathlib import Path

# Add backend directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from core.config import settings


# WCAG 2.1 Level A and AA Success Criteria
# Total: 50 criteria (30 Level A, 20 Level AA)
WCAG_CRITERIA = [
    # Principle 1: Perceivable
    # Guideline 1.1 Text Alternatives
    ("1.1.1", "Non-text Content", "A", "2.1", "All non-text content has a text alternative that serves the equivalent purpose.", "https://www.w3.org/WAI/WCAG21/Understanding/non-text-content.html"),

    # Guideline 1.2 Time-based Media
    ("1.2.1", "Audio-only and Video-only (Prerecorded)", "A", "2.1", "For prerecorded audio-only and video-only media, alternatives are provided.", "https://www.w3.org/WAI/WCAG21/Understanding/audio-only-and-video-only-prerecorded.html"),
    ("1.2.2", "Captions (Prerecorded)", "A", "2.1", "Captions are provided for all prerecorded audio content in synchronized media.", "https://www.w3.org/WAI/WCAG21/Understanding/captions-prerecorded.html"),
    ("1.2.3", "Audio Description or Media Alternative (Prerecorded)", "A", "2.1", "An alternative or audio description is provided for prerecorded synchronized media.", "https://www.w3.org/WAI/WCAG21/Understanding/audio-description-or-media-alternative-prerecorded.html"),
    ("1.2.4", "Captions (Live)", "AA", "2.1", "Captions are provided for all live audio content in synchronized media.", "https://www.w3.org/WAI/WCAG21/Understanding/captions-live.html"),
    ("1.2.5", "Audio Description (Prerecorded)", "AA", "2.1", "Audio description is provided for all prerecorded video content in synchronized media.", "https://www.w3.org/WAI/WCAG21/Understanding/audio-description-prerecorded.html"),

    # Guideline 1.3 Adaptable
    ("1.3.1", "Info and Relationships", "A", "2.1", "Information, structure, and relationships conveyed through presentation can be programmatically determined.", "https://www.w3.org/WAI/WCAG21/Understanding/info-and-relationships.html"),
    ("1.3.2", "Meaningful Sequence", "A", "2.1", "When the sequence affects meaning, a correct reading sequence can be programmatically determined.", "https://www.w3.org/WAI/WCAG21/Understanding/meaningful-sequence.html"),
    ("1.3.3", "Sensory Characteristics", "A", "2.1", "Instructions do not rely solely on sensory characteristics of components.", "https://www.w3.org/WAI/WCAG21/Understanding/sensory-characteristics.html"),
    ("1.3.4", "Orientation", "AA", "2.1", "Content does not restrict its view and operation to a single display orientation.", "https://www.w3.org/WAI/WCAG21/Understanding/orientation.html"),
    ("1.3.5", "Identify Input Purpose", "AA", "2.1", "The purpose of input fields collecting user information can be programmatically determined.", "https://www.w3.org/WAI/WCAG21/Understanding/identify-input-purpose.html"),

    # Guideline 1.4 Distinguishable
    ("1.4.1", "Use of Color", "A", "2.1", "Color is not used as the only visual means of conveying information.", "https://www.w3.org/WAI/WCAG21/Understanding/use-of-color.html"),
    ("1.4.2", "Audio Control", "A", "2.1", "If audio plays automatically for more than 3 seconds, a mechanism is available to pause, stop, or control volume.", "https://www.w3.org/WAI/WCAG21/Understanding/audio-control.html"),
    ("1.4.3", "Contrast (Minimum)", "AA", "2.1", "Text has a contrast ratio of at least 4.5:1 (3:1 for large text).", "https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.html"),
    ("1.4.4", "Resize Text", "AA", "2.1", "Text can be resized without assistive technology up to 200% without loss of content or functionality.", "https://www.w3.org/WAI/WCAG21/Understanding/resize-text.html"),
    ("1.4.5", "Images of Text", "AA", "2.1", "If the technologies can achieve the visual presentation, text is used rather than images of text.", "https://www.w3.org/WAI/WCAG21/Understanding/images-of-text.html"),
    ("1.4.10", "Reflow", "AA", "2.1", "Content can be presented without loss of information or functionality and without scrolling in two dimensions.", "https://www.w3.org/WAI/WCAG21/Understanding/reflow.html"),
    ("1.4.11", "Non-text Contrast", "AA", "2.1", "Visual presentation of UI components and graphical objects have a contrast ratio of at least 3:1.", "https://www.w3.org/WAI/WCAG21/Understanding/non-text-contrast.html"),
    ("1.4.12", "Text Spacing", "AA", "2.1", "No loss of content or functionality occurs when users adjust text spacing.", "https://www.w3.org/WAI/WCAG21/Understanding/text-spacing.html"),
    ("1.4.13", "Content on Hover or Focus", "AA", "2.1", "Additional content triggered by hover or focus is dismissible, hoverable, and persistent.", "https://www.w3.org/WAI/WCAG21/Understanding/content-on-hover-or-focus.html"),

    # Principle 2: Operable
    # Guideline 2.1 Keyboard Accessible
    ("2.1.1", "Keyboard", "A", "2.1", "All functionality is operable through a keyboard interface.", "https://www.w3.org/WAI/WCAG21/Understanding/keyboard.html"),
    ("2.1.2", "No Keyboard Trap", "A", "2.1", "If keyboard focus can be moved to a component, focus can be moved away using only a keyboard.", "https://www.w3.org/WAI/WCAG21/Understanding/no-keyboard-trap.html"),
    ("2.1.4", "Character Key Shortcuts", "A", "2.1", "If a keyboard shortcut uses only character keys, it can be turned off or remapped.", "https://www.w3.org/WAI/WCAG21/Understanding/character-key-shortcuts.html"),

    # Guideline 2.2 Enough Time
    ("2.2.1", "Timing Adjustable", "A", "2.1", "For time limits, users can turn off, adjust, or extend the time.", "https://www.w3.org/WAI/WCAG21/Understanding/timing-adjustable.html"),
    ("2.2.2", "Pause, Stop, Hide", "A", "2.1", "For moving, blinking, scrolling, or auto-updating information, users can pause, stop, or hide it.", "https://www.w3.org/WAI/WCAG21/Understanding/pause-stop-hide.html"),

    # Guideline 2.3 Seizures and Physical Reactions
    ("2.3.1", "Three Flashes or Below Threshold", "A", "2.1", "Pages do not contain anything that flashes more than three times in any one second period.", "https://www.w3.org/WAI/WCAG21/Understanding/three-flashes-or-below-threshold.html"),

    # Guideline 2.4 Navigable
    ("2.4.1", "Bypass Blocks", "A", "2.1", "A mechanism is available to bypass blocks of content that are repeated on multiple pages.", "https://www.w3.org/WAI/WCAG21/Understanding/bypass-blocks.html"),
    ("2.4.2", "Page Titled", "A", "2.1", "Pages have titles that describe topic or purpose.", "https://www.w3.org/WAI/WCAG21/Understanding/page-titled.html"),
    ("2.4.3", "Focus Order", "A", "2.1", "If a page can be navigated sequentially, components receive focus in an order that preserves meaning.", "https://www.w3.org/WAI/WCAG21/Understanding/focus-order.html"),
    ("2.4.4", "Link Purpose (In Context)", "A", "2.1", "The purpose of each link can be determined from the link text alone or from context.", "https://www.w3.org/WAI/WCAG21/Understanding/link-purpose-in-context.html"),
    ("2.4.5", "Multiple Ways", "AA", "2.1", "More than one way is available to locate a page within a set of pages.", "https://www.w3.org/WAI/WCAG21/Understanding/multiple-ways.html"),
    ("2.4.6", "Headings and Labels", "AA", "2.1", "Headings and labels describe topic or purpose.", "https://www.w3.org/WAI/WCAG21/Understanding/headings-and-labels.html"),
    ("2.4.7", "Focus Visible", "AA", "2.1", "Any keyboard operable user interface has a mode of operation where the keyboard focus indicator is visible.", "https://www.w3.org/WAI/WCAG21/Understanding/focus-visible.html"),

    # Guideline 2.5 Input Modalities
    ("2.5.1", "Pointer Gestures", "A", "2.1", "All functionality that uses multipoint or path-based gestures can be operated with a single pointer.", "https://www.w3.org/WAI/WCAG21/Understanding/pointer-gestures.html"),
    ("2.5.2", "Pointer Cancellation", "A", "2.1", "For functionality operated with a single pointer, at least one of the following is true: no down-event, abort/undo, up reversal, or essential.", "https://www.w3.org/WAI/WCAG21/Understanding/pointer-cancellation.html"),
    ("2.5.3", "Label in Name", "A", "2.1", "For UI components with text labels, the name contains the text that is presented visually.", "https://www.w3.org/WAI/WCAG21/Understanding/label-in-name.html"),
    ("2.5.4", "Motion Actuation", "A", "2.1", "Functionality operated by device motion or user motion can also be operated by UI components.", "https://www.w3.org/WAI/WCAG21/Understanding/motion-actuation.html"),

    # Principle 3: Understandable
    # Guideline 3.1 Readable
    ("3.1.1", "Language of Page", "A", "2.1", "The default human language of each page can be programmatically determined.", "https://www.w3.org/WAI/WCAG21/Understanding/language-of-page.html"),
    ("3.1.2", "Language of Parts", "AA", "2.1", "The human language of each passage or phrase can be programmatically determined.", "https://www.w3.org/WAI/WCAG21/Understanding/language-of-parts.html"),

    # Guideline 3.2 Predictable
    ("3.2.1", "On Focus", "A", "2.1", "When any UI component receives focus, it does not initiate a change of context.", "https://www.w3.org/WAI/WCAG21/Understanding/on-focus.html"),
    ("3.2.2", "On Input", "A", "2.1", "Changing the setting of any UI component does not automatically cause a change of context.", "https://www.w3.org/WAI/WCAG21/Understanding/on-input.html"),
    ("3.2.3", "Consistent Navigation", "AA", "2.1", "Navigational mechanisms repeated on multiple pages occur in the same relative order.", "https://www.w3.org/WAI/WCAG21/Understanding/consistent-navigation.html"),
    ("3.2.4", "Consistent Identification", "AA", "2.1", "Components with the same functionality are identified consistently.", "https://www.w3.org/WAI/WCAG21/Understanding/consistent-identification.html"),

    # Guideline 3.3 Input Assistance
    ("3.3.1", "Error Identification", "A", "2.1", "If an input error is automatically detected, the item in error is identified and the error is described in text.", "https://www.w3.org/WAI/WCAG21/Understanding/error-identification.html"),
    ("3.3.2", "Labels or Instructions", "A", "2.1", "Labels or instructions are provided when content requires user input.", "https://www.w3.org/WAI/WCAG21/Understanding/labels-or-instructions.html"),
    ("3.3.3", "Error Suggestion", "AA", "2.1", "If an input error is detected and suggestions for correction are known, they are provided to the user.", "https://www.w3.org/WAI/WCAG21/Understanding/error-suggestion.html"),
    ("3.3.4", "Error Prevention (Legal, Financial, Data)", "AA", "2.1", "For pages with legal commitments or financial transactions, submissions are reversible, checked, or confirmed.", "https://www.w3.org/WAI/WCAG21/Understanding/error-prevention-legal-financial-data.html"),

    # Principle 4: Robust
    # Guideline 4.1 Compatible
    ("4.1.1", "Parsing", "A", "2.1", "In content using markup languages, elements have complete tags, are nested properly, and don't contain duplicate attributes.", "https://www.w3.org/WAI/WCAG21/Understanding/parsing.html"),
    ("4.1.2", "Name, Role, Value", "A", "2.1", "For all UI components, the name and role can be programmatically determined; states, properties, and values can be set.", "https://www.w3.org/WAI/WCAG21/Understanding/name-role-value.html"),
    ("4.1.3", "Status Messages", "AA", "2.1", "Status messages can be programmatically determined through role or properties so they can be presented without receiving focus.", "https://www.w3.org/WAI/WCAG21/Understanding/status-messages.html"),
]


async def seed_wcag_criteria():
    """Insert all WCAG 2.1 A and AA criteria into the database."""
    engine = create_async_engine(settings.database_url, echo=False)

    async with engine.begin() as conn:
        # Use raw SQL for upsert pattern
        insert_sql = text("""
            INSERT INTO wcag_criteria (criterion_id, name, level, wcag_version, description, understanding_url)
            VALUES (:criterion_id, :name, :level, :wcag_version, :description, :understanding_url)
            ON CONFLICT (criterion_id) DO NOTHING
        """)

        inserted = 0
        skipped = 0

        for criterion in WCAG_CRITERIA:
            result = await conn.execute(
                insert_sql,
                {
                    "criterion_id": criterion[0],
                    "name": criterion[1],
                    "level": criterion[2],
                    "wcag_version": criterion[3],
                    "description": criterion[4],
                    "understanding_url": criterion[5],
                },
            )
            if result.rowcount > 0:
                inserted += 1
            else:
                skipped += 1

        print(f"\n{'=' * 60}")
        print("WCAG 2.1 Criteria Seed Complete")
        print(f"{'=' * 60}")
        print(f"Total criteria:  {len(WCAG_CRITERIA)}")
        print(f"Inserted:        {inserted}")
        print(f"Skipped (exist): {skipped}")
        print(f"{'=' * 60}\n")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_wcag_criteria())
