from fastapi import APIRouter, HTTPException
from datetime import datetime, timezone
from sqlalchemy import text
import subprocess

from db.engine import engine
from core.config import settings

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    """
    Health check endpoint.
    Used by Docker healthchecks and load balancers.
    Returns 200 when the API process is running.
    """
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "accessibility-platform-api",
    }


@router.get("/health/db")
async def db_health_check():
    """
    Database health check endpoint.
    Verifies database connection and lists existing tables.
    """
    db_url = settings.database_url
    # Mask password for logging
    masked_url = db_url
    if "@" in db_url:
        parts = db_url.split("@")
        prefix = parts[0]
        if ":" in prefix:
            scheme_user = prefix.rsplit(":", 1)[0]
            masked_url = f"{scheme_user}:***@{parts[1]}"

    try:
        async with engine.begin() as conn:
            # Check connection
            result = await conn.execute(text("SELECT 1"))
            result.fetchone()

            # List tables
            tables_result = await conn.execute(text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tables = [row[0] for row in tables_result.fetchall()]

            # Check alembic version
            alembic_version = None
            try:
                version_result = await conn.execute(text(
                    "SELECT version_num FROM alembic_version LIMIT 1"
                ))
                row = version_result.fetchone()
                if row:
                    alembic_version = row[0]
            except Exception:
                pass  # Table might not exist yet

        return {
            "status": "ok",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "database_url": masked_url,
            "connection": "success",
            "tables": tables,
            "table_count": len(tables),
            "alembic_version": alembic_version,
            "migrations_applied": alembic_version is not None,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "database_url": masked_url,
                "error": str(e),
                "error_type": type(e).__name__,
            },
        )


@router.post("/setup/migrate")
async def run_migrations():
    """
    Manually trigger database migrations.

    Call this endpoint after deployment if migrations didn't run automatically.
    This runs 'alembic upgrade head' to apply all pending migrations.
    """
    try:
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            capture_output=True,
            text=True,
            timeout=120,
        )

        if result.returncode == 0:
            return {
                "status": "success",
                "message": "Migrations completed successfully",
                "stdout": result.stdout.strip(),
            }
        else:
            raise HTTPException(
                status_code=500,
                detail={
                    "status": "error",
                    "message": "Migration failed",
                    "returncode": result.returncode,
                    "stdout": result.stdout.strip(),
                    "stderr": result.stderr.strip(),
                },
            )
    except subprocess.TimeoutExpired:
        raise HTTPException(
            status_code=500,
            detail={"status": "error", "message": "Migration timed out after 120s"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"status": "error", "message": str(e), "error_type": type(e).__name__},
        )


# WCAG 2.1 Level A and AA criteria (embedded to avoid import issues)
WCAG_CRITERIA = [
    # Principle 1: Perceivable
    ("1.1.1", "Non-text Content", "A", "2.1", "All non-text content has a text alternative.", "https://www.w3.org/WAI/WCAG21/Understanding/non-text-content.html"),
    ("1.2.1", "Audio-only and Video-only (Prerecorded)", "A", "2.1", "Alternatives are provided for prerecorded audio-only and video-only content.", "https://www.w3.org/WAI/WCAG21/Understanding/audio-only-and-video-only-prerecorded.html"),
    ("1.2.2", "Captions (Prerecorded)", "A", "2.1", "Captions are provided for prerecorded audio content in synchronized media.", "https://www.w3.org/WAI/WCAG21/Understanding/captions-prerecorded.html"),
    ("1.2.3", "Audio Description or Media Alternative (Prerecorded)", "A", "2.1", "An alternative or audio description is provided for prerecorded video.", "https://www.w3.org/WAI/WCAG21/Understanding/audio-description-or-media-alternative-prerecorded.html"),
    ("1.2.4", "Captions (Live)", "AA", "2.1", "Captions are provided for live audio content in synchronized media.", "https://www.w3.org/WAI/WCAG21/Understanding/captions-live.html"),
    ("1.2.5", "Audio Description (Prerecorded)", "AA", "2.1", "Audio description is provided for prerecorded video content.", "https://www.w3.org/WAI/WCAG21/Understanding/audio-description-prerecorded.html"),
    ("1.3.1", "Info and Relationships", "A", "2.1", "Information and relationships conveyed visually are programmatically determinable.", "https://www.w3.org/WAI/WCAG21/Understanding/info-and-relationships.html"),
    ("1.3.2", "Meaningful Sequence", "A", "2.1", "The correct reading sequence can be programmatically determined.", "https://www.w3.org/WAI/WCAG21/Understanding/meaningful-sequence.html"),
    ("1.3.3", "Sensory Characteristics", "A", "2.1", "Instructions don't rely solely on sensory characteristics.", "https://www.w3.org/WAI/WCAG21/Understanding/sensory-characteristics.html"),
    ("1.3.4", "Orientation", "AA", "2.1", "Content does not restrict its view and operation to a single display orientation.", "https://www.w3.org/WAI/WCAG21/Understanding/orientation.html"),
    ("1.3.5", "Identify Input Purpose", "AA", "2.1", "The purpose of input fields collecting user information can be programmatically determined.", "https://www.w3.org/WAI/WCAG21/Understanding/identify-input-purpose.html"),
    ("1.4.1", "Use of Color", "A", "2.1", "Color is not the only visual means of conveying information.", "https://www.w3.org/WAI/WCAG21/Understanding/use-of-color.html"),
    ("1.4.2", "Audio Control", "A", "2.1", "A mechanism is available to pause or stop audio that plays automatically.", "https://www.w3.org/WAI/WCAG21/Understanding/audio-control.html"),
    ("1.4.3", "Contrast (Minimum)", "AA", "2.1", "Text has a contrast ratio of at least 4.5:1.", "https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.html"),
    ("1.4.4", "Resize Text", "AA", "2.1", "Text can be resized up to 200% without loss of functionality.", "https://www.w3.org/WAI/WCAG21/Understanding/resize-text.html"),
    ("1.4.5", "Images of Text", "AA", "2.1", "Text is used instead of images of text when possible.", "https://www.w3.org/WAI/WCAG21/Understanding/images-of-text.html"),
    ("1.4.10", "Reflow", "AA", "2.1", "Content can be presented without horizontal scrolling at 320px width.", "https://www.w3.org/WAI/WCAG21/Understanding/reflow.html"),
    ("1.4.11", "Non-text Contrast", "AA", "2.1", "UI components and graphics have a contrast ratio of at least 3:1.", "https://www.w3.org/WAI/WCAG21/Understanding/non-text-contrast.html"),
    ("1.4.12", "Text Spacing", "AA", "2.1", "No loss of content when text spacing is adjusted.", "https://www.w3.org/WAI/WCAG21/Understanding/text-spacing.html"),
    ("1.4.13", "Content on Hover or Focus", "AA", "2.1", "Additional content on hover/focus is dismissible, hoverable, and persistent.", "https://www.w3.org/WAI/WCAG21/Understanding/content-on-hover-or-focus.html"),
    # Principle 2: Operable
    ("2.1.1", "Keyboard", "A", "2.1", "All functionality is available from a keyboard.", "https://www.w3.org/WAI/WCAG21/Understanding/keyboard.html"),
    ("2.1.2", "No Keyboard Trap", "A", "2.1", "Keyboard focus can be moved away from any component.", "https://www.w3.org/WAI/WCAG21/Understanding/no-keyboard-trap.html"),
    ("2.1.4", "Character Key Shortcuts", "A", "2.1", "Single character key shortcuts can be turned off or remapped.", "https://www.w3.org/WAI/WCAG21/Understanding/character-key-shortcuts.html"),
    ("2.2.1", "Timing Adjustable", "A", "2.1", "Time limits can be turned off, adjusted, or extended.", "https://www.w3.org/WAI/WCAG21/Understanding/timing-adjustable.html"),
    ("2.2.2", "Pause, Stop, Hide", "A", "2.1", "Moving, blinking, or auto-updating content can be paused, stopped, or hidden.", "https://www.w3.org/WAI/WCAG21/Understanding/pause-stop-hide.html"),
    ("2.3.1", "Three Flashes or Below Threshold", "A", "2.1", "Content does not flash more than 3 times per second.", "https://www.w3.org/WAI/WCAG21/Understanding/three-flashes-or-below-threshold.html"),
    ("2.4.1", "Bypass Blocks", "A", "2.1", "A mechanism is available to bypass repeated content.", "https://www.w3.org/WAI/WCAG21/Understanding/bypass-blocks.html"),
    ("2.4.2", "Page Titled", "A", "2.1", "Web pages have descriptive titles.", "https://www.w3.org/WAI/WCAG21/Understanding/page-titled.html"),
    ("2.4.3", "Focus Order", "A", "2.1", "Focusable components receive focus in a meaningful sequence.", "https://www.w3.org/WAI/WCAG21/Understanding/focus-order.html"),
    ("2.4.4", "Link Purpose (In Context)", "A", "2.1", "The purpose of each link can be determined from link text or context.", "https://www.w3.org/WAI/WCAG21/Understanding/link-purpose-in-context.html"),
    ("2.4.5", "Multiple Ways", "AA", "2.1", "More than one way is available to locate a page within a site.", "https://www.w3.org/WAI/WCAG21/Understanding/multiple-ways.html"),
    ("2.4.6", "Headings and Labels", "AA", "2.1", "Headings and labels describe topic or purpose.", "https://www.w3.org/WAI/WCAG21/Understanding/headings-and-labels.html"),
    ("2.4.7", "Focus Visible", "AA", "2.1", "Keyboard focus indicator is visible.", "https://www.w3.org/WAI/WCAG21/Understanding/focus-visible.html"),
    ("2.5.1", "Pointer Gestures", "A", "2.1", "Multipoint or path-based gestures have single-pointer alternatives.", "https://www.w3.org/WAI/WCAG21/Understanding/pointer-gestures.html"),
    ("2.5.2", "Pointer Cancellation", "A", "2.1", "Functions triggered by pointer can be aborted or undone.", "https://www.w3.org/WAI/WCAG21/Understanding/pointer-cancellation.html"),
    ("2.5.3", "Label in Name", "A", "2.1", "Accessible names contain the visible label text.", "https://www.w3.org/WAI/WCAG21/Understanding/label-in-name.html"),
    ("2.5.4", "Motion Actuation", "A", "2.1", "Device motion functionality can be operated without motion.", "https://www.w3.org/WAI/WCAG21/Understanding/motion-actuation.html"),
    # Principle 3: Understandable
    ("3.1.1", "Language of Page", "A", "2.1", "The default human language of each page can be programmatically determined.", "https://www.w3.org/WAI/WCAG21/Understanding/language-of-page.html"),
    ("3.1.2", "Language of Parts", "AA", "2.1", "The language of each passage or phrase can be programmatically determined.", "https://www.w3.org/WAI/WCAG21/Understanding/language-of-parts.html"),
    ("3.2.1", "On Focus", "A", "2.1", "Receiving focus does not initiate a change of context.", "https://www.w3.org/WAI/WCAG21/Understanding/on-focus.html"),
    ("3.2.2", "On Input", "A", "2.1", "Changing a setting does not automatically change context unless user is advised.", "https://www.w3.org/WAI/WCAG21/Understanding/on-input.html"),
    ("3.2.3", "Consistent Navigation", "AA", "2.1", "Navigation mechanisms are consistent across pages.", "https://www.w3.org/WAI/WCAG21/Understanding/consistent-navigation.html"),
    ("3.2.4", "Consistent Identification", "AA", "2.1", "Components with same functionality are identified consistently.", "https://www.w3.org/WAI/WCAG21/Understanding/consistent-identification.html"),
    ("3.3.1", "Error Identification", "A", "2.1", "Input errors are automatically detected and described in text.", "https://www.w3.org/WAI/WCAG21/Understanding/error-identification.html"),
    ("3.3.2", "Labels or Instructions", "A", "2.1", "Labels or instructions are provided when content requires user input.", "https://www.w3.org/WAI/WCAG21/Understanding/labels-or-instructions.html"),
    ("3.3.3", "Error Suggestion", "AA", "2.1", "Suggestions for correction are provided when errors are detected.", "https://www.w3.org/WAI/WCAG21/Understanding/error-suggestion.html"),
    ("3.3.4", "Error Prevention (Legal, Financial, Data)", "AA", "2.1", "Submissions are reversible, checked, or confirmed for legal/financial pages.", "https://www.w3.org/WAI/WCAG21/Understanding/error-prevention-legal-financial-data.html"),
    # Principle 4: Robust
    ("4.1.1", "Parsing", "A", "2.1", "Elements have complete tags, proper nesting, and no duplicate attributes.", "https://www.w3.org/WAI/WCAG21/Understanding/parsing.html"),
    ("4.1.2", "Name, Role, Value", "A", "2.1", "UI component names and roles can be programmatically determined.", "https://www.w3.org/WAI/WCAG21/Understanding/name-role-value.html"),
    ("4.1.3", "Status Messages", "AA", "2.1", "Status messages can be programmatically determined without receiving focus.", "https://www.w3.org/WAI/WCAG21/Understanding/status-messages.html"),
]


@router.post("/setup/seed-wcag")
async def seed_wcag_data():
    """
    Seed WCAG criteria data.

    Call this endpoint once after initial deployment to populate
    the WCAG success criteria table. Safe to call multiple times
    (uses upsert logic with ON CONFLICT DO NOTHING).
    """
    try:
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

        return {
            "status": "success",
            "message": "WCAG criteria seeded successfully",
            "total": len(WCAG_CRITERIA),
            "inserted": inserted,
            "skipped": skipped,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"status": "error", "message": str(e)},
        )
