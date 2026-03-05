"""
Crawler Package

Website crawling utilities using Playwright for page discovery.
"""

from crawler.robots import USER_AGENT, can_fetch, fetch_robots_parser
from crawler.spider import PageData, classify_page_type, crawl, normalise_url

__all__ = [
    "USER_AGENT",
    "can_fetch",
    "fetch_robots_parser",
    "PageData",
    "classify_page_type",
    "crawl",
    "normalise_url",
]
