"""
robots.txt Helper Module

Provides utilities for fetching and parsing robots.txt files
to ensure the crawler respects website crawling policies.
"""

import urllib.robotparser
from urllib.parse import urljoin, urlparse

import httpx

from core.logging import get_logger

logger = get_logger(__name__)

# User agent string for the crawler
USER_AGENT = "A11yBot/1.0 (+https://a11y-platform.dev/bot)"


async def fetch_robots_parser(base_url: str) -> urllib.robotparser.RobotFileParser | None:
    """
    Fetch and parse robots.txt from a given base URL.

    Constructs the robots.txt URL from base_url and fetches it using httpx.
    Parses the content with RobotFileParser.

    Args:
        base_url: The base URL of the website (e.g., https://example.com)

    Returns:
        RobotFileParser instance on success, None on any error.
        Never raises - always returns.
    """
    try:
        # Parse the base URL to construct robots.txt URL
        parsed = urlparse(base_url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

        logger.debug("fetching_robots_txt", url=robots_url)

        # Fetch robots.txt with timeout
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            response = await client.get(
                robots_url,
                headers={"User-Agent": USER_AGENT}
            )

            # Check for successful response
            if response.status_code != 200:
                logger.debug(
                    "robots_txt_not_found",
                    url=robots_url,
                    status_code=response.status_code
                )
                return None

            # Parse the robots.txt content
            parser = urllib.robotparser.RobotFileParser()
            parser.set_url(robots_url)
            parser.parse(response.text.splitlines())

            logger.debug("robots_txt_parsed", url=robots_url)
            return parser

    except httpx.TimeoutException:
        logger.debug("robots_txt_timeout", url=base_url)
        return None
    except httpx.RequestError as e:
        logger.debug("robots_txt_request_error", url=base_url, error=str(e))
        return None
    except Exception as e:
        logger.debug("robots_txt_parse_error", url=base_url, error=str(e))
        return None


def can_fetch(
    parser: urllib.robotparser.RobotFileParser | None,
    url: str,
    user_agent: str = "A11yBot"
) -> bool:
    """
    Check if the given URL can be fetched according to robots.txt rules.

    Args:
        parser: The RobotFileParser instance (can be None)
        url: The URL to check
        user_agent: The user agent string to check against

    Returns:
        True if the URL can be fetched, False otherwise.
        If parser is None, returns True (assume allowed).
    """
    if parser is None:
        return True

    try:
        return parser.can_fetch(user_agent, url)
    except Exception:
        # On any parsing error, allow the fetch
        return True
