"""
Betking implementation using Playwright for browser automation.
This bypasses Cloudflare bot protection by using a real browser.

Installation:
    pip install playwright
    playwright install chromium

Usage:
    from NaijaBet_Api.bookmakers.betking_playwright import BetkingPlaywright
    from NaijaBet_Api.id import Betid

    betking = BetkingPlaywright()
    data = betking.get_league(Betid.PREMIERLEAGUE)
    print(f"Got {len(data)} matches")
"""

from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page
from NaijaBet_Api.bookmakers.betking import Betking
from NaijaBet_Api.id import Betid
from typing import List, Dict, Any, Optional
import json


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

    def __init__(self, headless: bool = True, timeout: int = 30000):
        """
        Initialize Betking with Playwright browser automation.

        Args:
            headless: Run browser in headless mode (default: True)
            timeout: Request timeout in milliseconds (default: 30000)
        """
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
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
            ]
        )

        # Create context with realistic browser fingerprint
        self.context = self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='en-US',
            timezone_id='America/New_York',
        )

        # Set extra headers
        self.context.set_extra_http_headers({
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': 'https://betking.com/',
        })

        # Create page
        self.page = self.context.new_page()
        self.page.set_default_timeout(self.timeout)

        # Visit main site to establish session and get past Cloudflare
        print("Loading Betking site...")
        self.page.goto('https://betking.com/sports', wait_until='networkidle')
        print("Browser session established")

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
        """
        # Start browser if not already started
        if self.browser is None:
            self._start_browser()

        try:
            # Construct API URL
            api_url = league.to_endpoint(self.site)

            print(f"Fetching: {api_url}")

            # Use browser's request context to fetch API
            response = self.page.request.get(api_url)

            if response.status != 200:
                print(f"Warning: HTTP {response.status} for {api_url}")
                return []

            # Parse JSON response
            try:
                data = response.json()
                # Normalize the data using parent class method
                return self.normalizer(data)
            except Exception as e:
                print(f"Error parsing JSON: {e}")
                return []

        except Exception as e:
            print(f"Error fetching league: {e}")
            return []

    def get_all(self) -> List[Dict[str, Any]]:
        """
        Get all leagues' odds using browser automation.

        Returns:
            List of all matches from all implemented leagues
        """
        if self.browser is None:
            self._start_browser()

        self.data = []
        for league in Betid:
            league_data = self.get_league(league)
            if league_data:
                self.data.extend(league_data)

        return self.data

    def get_team(self, team: str) -> List[Dict[str, Any]]:
        """
        Get odds for matches involving a specific team.

        Args:
            team: Team name to search for

        Returns:
            List of matches involving the team
        """
        all_matches = self.get_all()

        def filter_func(data):
            match: str = data["match"]
            return match.lower().find(team.lower()) != -1

        return list(filter(filter_func, all_matches))


def example_usage():
    """Example of how to use BetkingPlaywright"""

    # Method 1: Using context manager (recommended)
    print("=" * 70)
    print("Method 1: Using context manager")
    print("=" * 70)

    with BetkingPlaywright(headless=True) as betking:
        # Get Premier League odds
        pl_data = betking.get_league(Betid.PREMIERLEAGUE)
        print(f"\nPremier League: {len(pl_data)} matches")
        if pl_data:
            print(f"First match: {pl_data[0]['match']}")
            print(f"Odds: {pl_data[0].get('home')} / {pl_data[0].get('draw')} / {pl_data[0].get('away')}")

        # Get La Liga odds
        ll_data = betking.get_league(Betid.LALIGA)
        print(f"\nLa Liga: {len(ll_data)} matches")

        # Search for specific team
        arsenal_matches = betking.get_team("Arsenal")
        print(f"\nArsenal matches: {len(arsenal_matches)}")

    # Browser automatically closed after context manager exits

    print("\n" + "=" * 70)
    print("Method 2: Manual management")
    print("=" * 70)

    # Method 2: Manual browser management
    betking = BetkingPlaywright(headless=True)
    betking._start_browser()

    try:
        data = betking.get_league(Betid.BUNDESLIGA)
        print(f"\nBundesliga: {len(data)} matches")
    finally:
        betking._stop_browser()


if __name__ == "__main__":
    example_usage()
