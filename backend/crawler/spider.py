"""
Playwright Spider Module

Async web crawler using Playwright for page discovery.
Implements BFS crawling with robots.txt respect and URL normalization.
"""

import re
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse, urlunparse

import httpx
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

from core.logging import get_logger
from crawler.robots import USER_AGENT, can_fetch, fetch_robots_parser

logger = get_logger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# FIX 6: Route blocking patterns for speed optimization
# ─────────────────────────────────────────────────────────────────────────────
BLOCKED_RESOURCE_PATTERNS = [
    "google-analytics",
    "googletagmanager",
    "facebook.net",
    "hotjar",
    "intercom",
    "crisp.chat",
    "fonts.googleapis",
    "doubleclick.net",
    "googlesyndication",
    "segment.com",
    "mixpanel.com",
    "amplitude.com",
    "fullstory.com",
    "newrelic.com",
    "sentry.io",
    "cloudflareinsights",
]


@dataclass
class PageData:
    """Data class representing a discovered page."""
    url: str
    title: str
    http_status: int
    page_type: str
    error: Optional[str] = None


# File extensions to skip during crawling
SKIP_EXTENSIONS = frozenset([
    '.pdf', '.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp', '.ico',
    '.css', '.js', '.xml', '.zip', '.tar', '.gz', '.rar',
    '.mp3', '.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm',
    '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
    '.woff', '.woff2', '.ttf', '.eot', '.otf'
])


def classify_page_type(url: str, title: str, http_status: int = 200) -> str:
    """
    Classify the type of page based on URL and title.

    Args:
        url: The page URL
        title: The page title
        http_status: The HTTP status code

    Returns:
        One of: home, form, navigation, media, search, auth, error, other
    """
    url_lower = url.lower()
    title_lower = (title or "").lower()

    # Parse URL path
    parsed = urlparse(url_lower)
    path = parsed.path.rstrip('/')

    # Check for HTTP error status
    if http_status >= 400:
        return "error"

    # Home page detection
    if path == "" or path == "/":
        return "home"

    # Form-related pages
    form_keywords = ['contact', 'about', 'form', 'apply', 'register', 'signup', 'sign-up', 'subscribe']
    if any(kw in url_lower or kw in title_lower for kw in form_keywords):
        return "form"

    # Search pages
    search_keywords = ['search', 'find', 'results', 'query']
    if any(kw in url_lower for kw in search_keywords):
        return "search"

    # Auth pages
    auth_keywords = ['login', 'signin', 'sign-in', 'auth', 'logout', 'password', 'account']
    if any(kw in url_lower for kw in auth_keywords):
        return "auth"

    # Navigation pages
    nav_keywords = ['nav', 'menu', 'sitemap', 'index', 'directory']
    if any(kw in url_lower for kw in nav_keywords):
        return "navigation"

    # Media pages
    media_keywords = ['video', 'audio', 'media', 'gallery', 'image', 'photo', 'podcast']
    if any(kw in url_lower for kw in media_keywords):
        return "media"

    return "other"


def normalise_url(url: str, base_domain: str) -> Optional[str]:
    """
    Normalize a URL for deduplication and filtering.

    Args:
        url: The URL to normalize
        base_domain: The base domain (scheme + netloc) to match against

    Returns:
        Normalized URL or None if the URL should be rejected
    """
    try:
        parsed = urlparse(url)
        base_parsed = urlparse(base_domain)

        # Reject non-HTTP(S) schemes
        if parsed.scheme not in ('http', 'https'):
            return None

        # Reject different domains
        if parsed.netloc.lower() != base_parsed.netloc.lower():
            return None

        # Reject file extensions we don't want to crawl
        path_lower = parsed.path.lower()
        for ext in SKIP_EXTENSIONS:
            if path_lower.endswith(ext):
                return None

        # Strip fragment and query string, normalize path
        # Strip trailing slash to avoid duplicates (e.g., /about/ == /about)
        path = parsed.path.rstrip('/') or '/'
        normalized = urlunparse((
            parsed.scheme,
            parsed.netloc.lower(),
            path,
            '',  # params
            '',  # query
            ''   # fragment
        ))

        return normalized

    except Exception:
        return None


async def check_content_type(url: str) -> Optional[str]:
    """
    Send a HEAD request to check the Content-Type of a URL.

    Args:
        url: The URL to check

    Returns:
        Content-Type header value or None on error
    """
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            response = await client.head(url, headers={'User-Agent': USER_AGENT})
            return response.headers.get('content-type', '')
    except Exception:
        return None


def is_html_content_type(content_type: Optional[str]) -> bool:
    """Check if a Content-Type header indicates HTML content."""
    if not content_type:
        return True  # Assume HTML if we can't determine
    content_type = content_type.lower()
    return 'text/html' in content_type or 'application/xhtml' in content_type


async def crawl(
    start_url: str,
    max_pages: int = 15,
    respect_robots: bool = True
) -> list[PageData]:
    """
    Crawl a website starting from the given URL using BFS.

    Args:
        start_url: The URL to start crawling from
        max_pages: Maximum number of pages to discover
        respect_robots: Whether to respect robots.txt rules

    Returns:
        List of PageData objects for discovered pages
    """
    # Parse start URL to get base domain
    parsed_start = urlparse(start_url)
    base_domain = f"{parsed_start.scheme}://{parsed_start.netloc}"

    logger.info(
        "crawl_starting",
        start_url=start_url,
        base_domain=base_domain,
        max_pages=max_pages,
        respect_robots=respect_robots
    )

    # Fetch robots.txt if needed
    robots_parser = None
    if respect_robots:
        robots_parser = await fetch_robots_parser(base_domain)
        if robots_parser:
            logger.debug("robots_txt_loaded", base_domain=base_domain)
        else:
            logger.debug("robots_txt_not_available", base_domain=base_domain)

    # BFS crawl state
    visited: set[str] = set()
    queue: list[str] = [normalise_url(start_url, base_domain) or start_url]
    results: list[PageData] = []

    browser = None
    context = None

    try:
        async with async_playwright() as playwright:
            # Launch browser with sandbox disabled for Docker compatibility
            browser = await playwright.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                    "--disable-extensions",
                    "--disable-background-networking",
                ]
            )

            # Create browser context with user agent
            context = await browser.new_context(
                user_agent=USER_AGENT,
                viewport={"width": 1280, "height": 800},
                ignore_https_errors=True,
            )

            # BFS loop
            while queue and len(results) < max_pages:
                current_url = queue.pop(0)

                # Skip if already visited
                if current_url in visited:
                    continue

                # Check robots.txt
                if respect_robots and not can_fetch(robots_parser, current_url):
                    logger.debug("url_blocked_by_robots", url=current_url)
                    continue

                # Verify same domain
                normalized = normalise_url(current_url, base_domain)
                if normalized is None:
                    continue

                current_url = normalized
                if current_url in visited:
                    continue

                visited.add(current_url)

                # Crawl the page
                page = None
                try:
                    page = await context.new_page()

                    # ─────────────────────────────────────────────────────────
                    # FIX 6: Set Accept-Language header to avoid redirect loops
                    # ─────────────────────────────────────────────────────────
                    await page.set_extra_http_headers({
                        "Accept-Language": "en-US,en;q=0.9"
                    })

                    # ─────────────────────────────────────────────────────────
                    # FIX 6: Block tracking/analytics scripts for faster crawl
                    # ─────────────────────────────────────────────────────────
                    async def handle_route(route):
                        request_url = route.request.url.lower()
                        if any(pattern in request_url for pattern in BLOCKED_RESOURCE_PATTERNS):
                            await route.abort()
                        else:
                            await route.continue_()

                    await page.route("**/*", handle_route)

                    # Check Content-Type via HEAD request before loading
                    content_type = await check_content_type(current_url)
                    if not is_html_content_type(content_type):
                        logger.debug(
                            "skipping_non_html",
                            url=current_url,
                            content_type=content_type
                        )
                        continue

                    # ─────────────────────────────────────────────────────────
                    # FIX 6: Use domcontentloaded + short settle time
                    # ─────────────────────────────────────────────────────────
                    # Navigate to the page with timeout handling
                    try:
                        response = await page.goto(
                            current_url,
                            wait_until="domcontentloaded",
                            timeout=20000  # Reduced from 30s
                        )

                        # Short settle time — crawler only needs links, not full render
                        await page.wait_for_timeout(800)

                    except PlaywrightTimeoutError:
                        # Timeout: record error and continue
                        results.append(PageData(
                            url=current_url,
                            title="",
                            http_status=0,
                            page_type="error",
                            error="timeout"
                        ))
                        logger.warning(
                            "page_timeout",
                            url=current_url
                        )
                        continue

                    # Get the final URL after any redirects
                    final_url = page.url
                    final_url_normalized = normalise_url(final_url, base_domain)

                    # If redirected to a different URL, use the final URL
                    if final_url_normalized and final_url_normalized != current_url:
                        # Check if we've already visited the final URL
                        if final_url_normalized in visited:
                            continue
                        visited.add(final_url_normalized)
                        current_url = final_url_normalized

                    http_status = response.status if response else 0
                    title = await page.title() or ""

                    # Extract links from the page
                    try:
                        links = await page.eval_on_selector_all(
                            "a[href]",
                            "els => els.map(e => e.href)"
                        )
                    except Exception:
                        links = []

                    # Process discovered links
                    for link in links:
                        if not link or not isinstance(link, str):
                            continue

                        # Normalize and filter the link
                        normalized_link = normalise_url(link, base_domain)
                        if normalized_link is None:
                            continue

                        # Add to queue if not visited and not already queued
                        if normalized_link not in visited and normalized_link not in queue:
                            queue.append(normalized_link)

                    # Classify and record the page
                    page_type = classify_page_type(current_url, title, http_status)
                    results.append(PageData(
                        url=current_url,
                        title=title[:500] if title else "",  # Limit title length
                        http_status=http_status,
                        page_type=page_type,
                        error=None
                    ))

                    logger.debug(
                        "page_crawled",
                        url=current_url,
                        status=http_status,
                        type=page_type,
                        links_found=len(links)
                    )

                except PlaywrightTimeoutError:
                    # Timeout during page operations
                    results.append(PageData(
                        url=current_url,
                        title="",
                        http_status=0,
                        page_type="error",
                        error="timeout"
                    ))
                    logger.warning(
                        "page_timeout",
                        url=current_url
                    )

                except Exception as e:
                    # Record error but continue crawling
                    error_msg = str(e)[:200]
                    results.append(PageData(
                        url=current_url,
                        title="",
                        http_status=0,
                        page_type="error",
                        error=error_msg
                    ))
                    logger.warning(
                        "page_crawl_error",
                        url=current_url,
                        error=error_msg
                    )

                finally:
                    if page:
                        try:
                            await page.close()
                        except Exception:
                            pass

            # Ensure at least the root page is returned (for JS-heavy SPAs with no links)
            if len(results) == 0:
                normalized_start = normalise_url(start_url, base_domain) or start_url
                results.append(PageData(
                    url=normalized_start,
                    title="",
                    http_status=0,
                    page_type="home",
                    error="no_links_found"
                ))
                logger.info(
                    "crawl_returning_root_only",
                    start_url=start_url
                )

            logger.info(
                "crawl_completed",
                start_url=start_url,
                pages_found=len(results),
                pages_visited=len(visited)
            )

    except Exception as e:
        logger.error(
            "crawl_failed",
            start_url=start_url,
            error=str(e)
        )
        raise

    finally:
        # Clean up browser resources
        if context:
            try:
                await context.close()
            except Exception:
                pass
        if browser:
            try:
                await browser.close()
            except Exception:
                pass

    return results
