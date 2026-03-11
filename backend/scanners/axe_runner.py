"""
axe-core Runner Module.

Runs axe-core accessibility scans on web pages using Playwright.

IMPORTANT: Download axe.min.js before using this module:
    curl -o backend/scanners/axe.min.js https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.9.1/axe.min.js

OR generate from npm:
    node -e "require('fs').writeFileSync('backend/scanners/axe.min.js', require('fs').readFileSync(require.resolve('axe-core/axe.min.js')))"
"""

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from playwright.async_api import (
    async_playwright,
    Browser,
    BrowserContext,
    Page,
    TimeoutError as PlaywrightTimeoutError,
)

from core.config import settings
from core.logging import get_logger
from storage.operations import upload_bytes, StorageError

logger = get_logger(__name__)

# Path to the local axe-core script
AXE_SCRIPT_PATH = Path(__file__).parent / "axe.min.js"

# Browser launch arguments optimized for headless operation
BROWSER_ARGS = [
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    "--disable-extensions",
    "--disable-background-networking",
]


@dataclass
class AxeResult:
    """Result of an axe-core accessibility scan."""

    violations: list[dict]
    passes: list[dict]
    incomplete: list[dict]
    url: str
    screenshot_key: Optional[str]
    scan_failed: bool = False
    failure_reason: str = ""


async def run_axe_on_page(
    url: str,
    evaluation_id: str,
    page_id: str,
    context: Optional[BrowserContext] = None,
) -> AxeResult:
    """
    Run axe-core accessibility scan on a page.

    Launches a headless Chromium browser (or reuses provided context),
    navigates to the URL, takes a screenshot, injects axe-core, and runs
    the accessibility scan.

    Args:
        url: The URL to scan
        evaluation_id: The evaluation UUID (for screenshot storage path)
        page_id: The page UUID (for screenshot storage path)
        context: Optional shared BrowserContext. If provided, reuse it
            instead of launching a new browser (saves 2-4 seconds per page).

    Returns:
        AxeResult containing violations, passes, incomplete checks,
        screenshot key, and scan_failed/failure_reason on error.
    """
    start_time = time.time()
    browser: Optional[Browser] = None
    page: Optional[Page] = None
    playwright_instance = None
    screenshot_key: Optional[str] = None
    should_close_browser = False
    injection_method: Optional[str] = None

    try:
        # If no shared context provided, create our own browser
        if context is None:
            playwright_instance = await async_playwright().start()
            browser = await playwright_instance.chromium.launch(
                headless=True,
                args=BROWSER_ARGS,
            )
            context = await browser.new_context(
                viewport={"width": 1280, "height": 800},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 (compatible; A11yBot/1.0)",
                ignore_https_errors=True,
                java_script_enabled=True,
            )
            should_close_browser = True

        page = await context.new_page()

        logger.info(
            "axe_scan_starting",
            url=url,
            evaluation_id=evaluation_id,
            page_id=page_id,
            using_shared_context=not should_close_browser,
        )

        # Track if navigation succeeded - don't attempt axe on timed-out page
        navigation_succeeded = False

        # ─────────────────────────────────────────────────────────────────────
        # FIX 1: Two-stage page load strategy (faster & more reliable)
        # ─────────────────────────────────────────────────────────────────────
        # Stage 1: Navigate with domcontentloaded (fast, always fires)
        try:
            response = await page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=20000,
            )

            # Stage 2: Wait for the body to have actual content
            try:
                await page.wait_for_selector("body", timeout=5000)
                # Give JS frameworks 1.5s to render after DOM is ready
                await page.wait_for_timeout(1500)
            except Exception:
                # body selector timeout is non-fatal — continue with whatever rendered
                pass

            if response is None:
                logger.warning(
                    "axe_navigation_no_response",
                    url=url,
                )
            navigation_succeeded = True

        except PlaywrightTimeoutError:
            logger.error(
                "axe_navigation_timeout",
                url=url,
            )
            # Navigation timeout - take screenshot if possible but skip axe
            navigation_succeeded = False
        except Exception as nav_error:
            logger.warning(
                "axe_navigation_error",
                url=url,
                error=str(nav_error),
            )
            # Other navigation error - try to continue
            navigation_succeeded = True

        # Take screenshot (even on partial failure)
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

        # If navigation timed out, return with scan_failed=True
        if not navigation_succeeded:
            return AxeResult(
                violations=[],
                passes=[],
                incomplete=[],
                url=url,
                screenshot_key=screenshot_key,
                scan_failed=True,
                failure_reason="navigation timeout",
            )

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
                scan_failed=True,
                failure_reason="axe.min.js not found",
            )

        # ─────────────────────────────────────────────────────────────────────
        # FIX 2: Robust axe-core injection with fallback
        # ─────────────────────────────────────────────────────────────────────
        axe_injected = False

        # Method 1: Try script tag injection first (standard)
        try:
            await page.add_script_tag(path=str(AXE_SCRIPT_PATH))
            # Verify axe actually loaded
            axe_loaded = await page.evaluate("() => typeof axe !== 'undefined'")
            if axe_loaded:
                axe_injected = True
                injection_method = "script_tag"
                logger.debug("axe_script_tag_injected", url=url)
        except Exception as e:
            logger.warning("axe_script_tag_failed", url=url, error=str(e))

        # Method 2: Fallback — evaluate the axe source directly (bypasses CSP)
        if not axe_injected:
            try:
                axe_source = AXE_SCRIPT_PATH.read_text(encoding="utf-8")
                await page.evaluate(axe_source)
                axe_loaded = await page.evaluate("() => typeof axe !== 'undefined'")
                if axe_loaded:
                    axe_injected = True
                    injection_method = "evaluate_fallback"
                    logger.info("axe_injected_via_evaluate_fallback", url=url)
            except Exception as e:
                logger.error("axe_inject_fallback_failed", url=url, error=str(e))

        if not axe_injected:
            logger.error("axe_injection_completely_failed", url=url)
            return AxeResult(
                violations=[],
                passes=[],
                incomplete=[],
                url=url,
                screenshot_key=screenshot_key,
                scan_failed=True,
                failure_reason="axe injection failed",
            )

        # ─────────────────────────────────────────────────────────────────────
        # FIX 3: Reliable axe.run() call with timeout safety
        # ─────────────────────────────────────────────────────────────────────
        try:
            results = await page.evaluate("""
                () => new Promise((resolve, reject) => {
                    // Timeout safety: if axe hangs, reject after 15s
                    const timeout = setTimeout(() => reject(new Error('axe.run timeout')), 15000);
                    axe.run(
                        document,
                        {
                            runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa'] },
                            resultTypes: ['violations', 'incomplete'],
                            elementRef: false,
                            selectors: true,
                            ancestry: false,
                            xpath: false
                        },
                        (err, results) => {
                            clearTimeout(timeout);
                            if (err) reject(err);
                            else resolve(results);
                        }
                    );
                })
            """)
        except Exception as axe_error:
            logger.error(
                "axe_run_failed",
                url=url,
                error=str(axe_error),
            )
            return AxeResult(
                violations=[],
                passes=[],
                incomplete=[],
                url=url,
                screenshot_key=screenshot_key,
                scan_failed=True,
                failure_reason=f"axe.run() failed: {str(axe_error)[:100]}",
            )

        violations = results.get("violations", [])
        passes = results.get("passes", [])
        incomplete = results.get("incomplete", [])

        duration_ms = int((time.time() - start_time) * 1000)

        # ─────────────────────────────────────────────────────────────────────
        # FIX 8: Enhanced logging for diagnosis
        # ─────────────────────────────────────────────────────────────────────
        logger.info(
            "axe_scan_complete",
            url=url,
            violations_count=len(violations),
            incomplete_count=len(incomplete),
            passes_count=len(passes),
            injection_method=injection_method,
            duration_ms=duration_ms,
        )

        # When 0 violations found (useful to distinguish true-pass from silent failure)
        if len(violations) == 0:
            logger.info(
                "axe_zero_violations",
                url=url,
                note="Either site is accessible or axe failed silently — check scan_failed flag",
                incomplete_count=len(incomplete),
            )

        return AxeResult(
            violations=violations,
            passes=passes,
            incomplete=incomplete,
            url=url,
            screenshot_key=screenshot_key,
            scan_failed=False,
            failure_reason="",
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
            scan_failed=True,
            failure_reason=f"unexpected error: {str(e)[:100]}",
        )

    finally:
        # Always close page (but not context if shared)
        try:
            if page:
                await page.close()
        except Exception as cleanup_error:
            logger.warning(
                "axe_page_cleanup_error",
                error=str(cleanup_error),
            )

        # Only close browser if we created it ourselves
        if should_close_browser:
            try:
                if browser:
                    await browser.close()
                if playwright_instance:
                    await playwright_instance.stop()
            except Exception as cleanup_error:
                logger.warning(
                    "axe_browser_cleanup_error",
                    error=str(cleanup_error),
                )
