"""
Betking implementation using Playwright for browser automation.
This bypasses Cloudflare bot protection by using a real browser.

Installation:
    pip install playwright
    playwright install chromium

Usage:
    from NaijaBet_Api.bookmakers.betking_playwright import BetkingPlaywright
    from NaijaBet_Api.id import Betid

    with BetkingPlaywright() as betking:
        data = betking.get_league(Betid.PREMIERLEAGUE)

The class has no async path: ``async_get_league``, ``async_get_all``, and ``async_session``
raise ``NotImplementedError``. Failures raise the same exceptions as the other bookmakers.
"""

import logging
from typing import Any, Dict, List, NoReturn, Optional

import aiohttp
from playwright.sync_api import (
    Browser,
    BrowserContext,
    Page,
    sync_playwright,
)
from playwright.sync_api import (
    Error as PlaywrightError,
)
from playwright.sync_api import (
    TimeoutError as PlaywrightTimeoutError,
)

from NaijaBet_Api.bookmakers.betking import Betking
from NaijaBet_Api.exceptions import BookmakerTimeoutError, BookmakerUnreachableError, NaijaBetError
from NaijaBet_Api.id import Betid

logger = logging.getLogger(__name__)


class BetkingPlaywright(Betking):
    """
    Betking bookmaker implementation using Playwright for browser automation.

    This class extends the standard Betking class to use a real browser,
    bypassing Cloudflare's bot protection.

    Attributes:
        browser: Playwright browser instance
        context: Playwright browser context
        page: Playwright page instance
        headless: Whether to run browser in headless mode
    """

    _sports_url = "https://betking.com/sports"

    def __init__(self, headless: bool = True, timeout: int = 30000):
        """
        Initialize Betking with Playwright browser automation.

        Args:
            headless: Run browser in headless mode (default: True)
            timeout: Request timeout in milliseconds (default: 30000)
        """
        super().__init__(timeout=(timeout / 1000, timeout / 1000))
        self.site = self._site
        self.headless = headless
        self.timeout = timeout
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

    def __enter__(self):
        """Context manager entry - starts browser"""
        self._start_browser()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - stops browser"""
        self._stop_browser()

    def _start_browser(self):
        """Start Playwright browser with proper configuration"""
        if self.browser is not None:
            return  # Already started

        self.playwright = sync_playwright().start()

        # Launch browser with realistic settings
        self.browser = self.playwright.chromium.launch(
            headless=self.headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
            ],
        )

        # Create context with realistic browser fingerprint
        self.context = self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36",
            locale="en-US",
            timezone_id="America/New_York",
        )

        # Set extra headers
        self.context.set_extra_http_headers(
            {
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Referer": "https://betking.com/",
            }
        )

        # Create page
        self.page = self.context.new_page()
        self.page.set_default_timeout(self.timeout)

        # Visit main site to establish session and get past Cloudflare
        logger.info("loading %s", self._sports_url)
        response = self.page.goto(self._sports_url, wait_until="networkidle")
        status = response.status if response is not None else None
        if status == 200:
            logger.info("Browser session established")
        else:
            logger.warning("%s answered %s on browser start", self.site, status)

    def _stop_browser(self):
        """Stop Playwright browser and clean up"""
        if self.page:
            self.page.close()
            self.page = None
        if self.context:
            self.context.close()
            self.context = None
        if self.browser:
            self.browser.close()
            self.browser = None
        if self.playwright:
            self.playwright.stop()
            self.playwright = None

    def get_league(self, league: Betid = Betid.PREMIERLEAGUE) -> List[Dict[str, Any]]:
        """
        Get league odds using browser automation.

        Args:
            league: League to fetch (from Betid enum)

        Returns:
            List of match dictionaries with odds data

        Raises:
            BookmakerBlockedError: the bookmaker answered with a non-200 status.
            BookmakerUnreachableError: no response arrived; its ``BookmakerTimeoutError``
                subclass means the timeout elapsed.
            ResponseParseError: the body is not the expected JSON shape.
        """
        if self.browser is None:
            self._start_browser()
        if self.page is None:
            raise RuntimeError("Browser page is not started; call _start_browser() first")

        api_url = league.to_endpoint(self.site)
        logger.debug("fetching %s", api_url)
        try:
            response = self.page.request.get(api_url, timeout=self.timeout)
        except PlaywrightTimeoutError as exc:
            raise BookmakerTimeoutError(self.site, f"timed out after {self.timeout} ms") from exc
        except PlaywrightError as exc:
            raise BookmakerUnreachableError(self.site, str(exc)) from exc
        body = response.text()
        if response.status != 200:
            raise self._blocked(response.status, body)
        return self._parse(body)

    def get_all(self) -> List[Dict[str, Any]]:
        """Return the rows of every league, fetched serially on the calling thread.

        The base class's ``get_all`` fans the leagues out across a
        ``ThreadPoolExecutor``, but sync Playwright binds its driver to the thread
        that started it: a call from a worker thread raises
        ``greenlet.error: Cannot switch to a different thread``
        (source: playwright/sync_api/_generated.py). So this override reproduces the
        base method's contract -- same ``self.errors`` bookkeeping, same
        ``_all_failed()`` behaviour, no row de-duplication (the base sync ``get_all``
        does not de-dupe either; only ``async_get_all`` does) -- one league at a time.

        Raises:
            NaijaBetError: every league failed.
        """
        pairs: List[tuple] = []
        for league in Betid:
            try:
                result: Any = self.get_league(league)
            except NaijaBetError as exc:
                result = exc
            pairs.append((league, result))
        return self._ledger(pairs)

    # get_team (inherited) calls get_all above, so it also drives the browser serially.

    def async_get_league(
        self, league: Betid = Betid.PREMIERLEAGUE, async_session: aiohttp.ClientSession | None = None
    ) -> NoReturn:
        raise NotImplementedError("BetkingPlaywright has no async path; use get_league")

    def async_get_all(self) -> NoReturn:
        raise NotImplementedError("BetkingPlaywright has no async path; use get_all")

    @property
    def async_session(self) -> NoReturn:
        raise NotImplementedError("BetkingPlaywright has no async path; use get_league or get_all")
