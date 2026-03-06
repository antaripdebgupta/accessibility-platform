"""
axe-core Runner Module.

Runs axe-core accessibility scans on web pages using Playwright.

IMPORTANT: Run the following command to generate axe.min.js:
    node -e "require('fs').writeFileSync('backend/scanners/axe.min.js', require('fs').readFileSync(require.resolve('axe-core/axe.min.js')))"

OR download from:
    https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.9.1/axe.min.js
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from playwright.async_api import async_playwright, Browser, Page

from core.config import settings
from core.logging import get_logger
from storage.operations import upload_bytes, StorageError

logger = get_logger(__name__)

# Path to the local axe-core script
AXE_SCRIPT_PATH = Path(__file__).parent / "axe.min.js"


@dataclass
class AxeResult:
    """Result of an axe-core accessibility scan."""

    violations: list[dict]
    passes: list[dict]
    incomplete: list[dict]
    url: str
    screenshot_key: Optional[str]


async def run_axe_on_page(
    url: str,
    evaluation_id: str,
    page_id: str,
) -> AxeResult:
    """
    Run axe-core accessibility scan on a page.

    Launches a headless Chromium browser, navigates to the URL,
    takes a screenshot, injects axe-core, and runs the accessibility scan.

    Args:
        url: The URL to scan
        evaluation_id: The evaluation UUID (for screenshot storage path)
        page_id: The page UUID (for screenshot storage path)

    Returns:
        AxeResult containing violations, passes, incomplete checks, and screenshot key
    """
    browser: Optional[Browser] = None
    page: Optional[Page] = None
    screenshot_key: Optional[str] = None

    try:
        # Launch browser
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
            ],
        )

        # Create context and page
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
        )
        page = await context.new_page()

        logger.info(
            "axe_scan_starting",
            url=url,
            evaluation_id=evaluation_id,
            page_id=page_id,
        )

        # Navigate to page
        try:
            response = await page.goto(
                url,
                wait_until="networkidle",
                timeout=30000,
            )

            if response is None:
                logger.warning(
                    "axe_navigation_no_response",
                    url=url,
                )
        except Exception as nav_error:
            logger.warning(
                "axe_navigation_error",
                url=url,
                error=str(nav_error),
            )
            # Continue anyway - page might still be usable

        # Take screenshot
        try:
            screenshot_bytes = await page.screenshot(
                full_page=True,
                type="png",
            )

            # Upload to MinIO
            screenshot_object_key = f"{evaluation_id}/{page_id}.png"
            try:
                screenshot_key = upload_bytes(
                    bucket=settings.minio_bucket_screenshots,
                    key=screenshot_object_key,
                    data=screenshot_bytes,
                    content_type="image/png",
                )
                logger.info(
                    "axe_screenshot_uploaded",
                    key=screenshot_key,
                )
            except StorageError as storage_error:
                logger.error(
                    "axe_screenshot_upload_failed",
                    error=str(storage_error),
                )
                screenshot_key = None

        except Exception as screenshot_error:
            logger.error(
                "axe_screenshot_failed",
                url=url,
                error=str(screenshot_error),
            )
            screenshot_key = None

        # Check if axe.min.js exists
        if not AXE_SCRIPT_PATH.exists():
            logger.error(
                "axe_script_not_found",
                path=str(AXE_SCRIPT_PATH),
            )
            return AxeResult(
                violations=[],
                passes=[],
                incomplete=[],
                url=url,
                screenshot_key=screenshot_key,
            )

        # Inject axe-core
        await page.add_script_tag(path=str(AXE_SCRIPT_PATH))

        # Run axe-core scan
        results = await page.evaluate("""
            () => axe.run({
                runOnly: {
                    type: 'tag',
                    values: ['wcag2a', 'wcag2aa']
                }
            })
        """)

        violations = results.get("violations", [])
        passes = results.get("passes", [])
        incomplete = results.get("incomplete", [])

        logger.info(
            "axe_scan_completed",
            url=url,
            violations_count=len(violations),
            passes_count=len(passes),
            incomplete_count=len(incomplete),
        )

        return AxeResult(
            violations=violations,
            passes=passes,
            incomplete=incomplete,
            url=url,
            screenshot_key=screenshot_key,
        )

    except Exception as e:
        logger.error(
            "axe_scan_failed",
            url=url,
            evaluation_id=evaluation_id,
            page_id=page_id,
            error=str(e),
        )

        return AxeResult(
            violations=[],
            passes=[],
            incomplete=[],
            url=url,
            screenshot_key=screenshot_key,
        )

    finally:
        # Always close browser resources
        try:
            if page:
                await page.close()
            if browser:
                await browser.close()
            if 'playwright' in locals():
                await playwright.stop()
        except Exception as cleanup_error:
            logger.warning(
                "axe_cleanup_error",
                error=str(cleanup_error),
            )
