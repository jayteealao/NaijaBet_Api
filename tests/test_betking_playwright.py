"""
Tests for Betking Playwright integration.

NOTE: These tests require Playwright and a working network connection.
They will be skipped if Playwright is not installed or if network is unavailable.

Installation:
    pip install playwright
    playwright install chromium
"""

import pytest

try:
    from playwright.sync_api import Error as PlaywrightError
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

    from NaijaBet_Api.bookmakers.betking_playwright import BetkingPlaywright
    from NaijaBet_Api.exceptions import BookmakerTimeoutError, BookmakerUnreachableError
    from NaijaBet_Api.id import Betid

    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


@pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason="Playwright not installed")
class TestBetkingPlaywright:
    """Tests for Betking with Playwright browser automation"""

    pytestmark = pytest.mark.live_site

    @pytest.mark.timeout(60)
    def test_initialization(self):
        """Test that BetkingPlaywright initializes correctly"""
        betking = BetkingPlaywright(headless=True)
        assert betking is not None
        assert betking.site == "betking"
        assert betking.headless is True

    @pytest.mark.timeout(60)
    def test_context_manager(self):
        """Test that context manager works"""
        with BetkingPlaywright(headless=True) as betking:
            assert betking.browser is not None
            assert betking.context is not None
            assert betking.page is not None

        # Browser should be closed after exiting context
        assert betking.browser is None
        assert betking.page is None

    @pytest.mark.timeout(90)
    def test_get_league_premier_league(self):
        """Test getting Premier League odds with Playwright"""
        with BetkingPlaywright(headless=True) as betking:
            data = betking.get_league(Betid.PREMIERLEAGUE)

            assert isinstance(data, list), "get_league should return a list"
            assert len(data) > 0, "Should have match data from API"

            # Validate structure
            match = data[0]
            required_fields = ["match", "league", "time", "league_id", "match_id"]
            for field in required_fields:
                assert field in match, f"Match should have '{field}' field"

            # Check data types
            assert isinstance(match["match"], str)
            assert " - " in match["match"]
            assert isinstance(match["time"], int)

            # Check odds if present
            odds_fields = ["home", "draw", "away"]
            for field in odds_fields:
                if field in match:
                    assert isinstance(match[field], (int, float))
                    assert match[field] > 0

    @pytest.mark.timeout(90)
    def test_get_multiple_leagues(self):
        """Test getting multiple leagues"""
        with BetkingPlaywright(headless=True) as betking:
            pl_data = betking.get_league(Betid.PREMIERLEAGUE)
            ll_data = betking.get_league(Betid.LALIGA)

            assert isinstance(pl_data, list)
            assert isinstance(ll_data, list)

            # At least one should have data
            assert len(pl_data) > 0 or len(ll_data) > 0

    @pytest.mark.timeout(180)
    def test_get_all(self):
        """Test getting all leagues"""
        with BetkingPlaywright(headless=True) as betking:
            data = betking.get_all()

            assert isinstance(data, list)
            assert len(data) > 0, "Should have data from at least one league"

    @pytest.mark.timeout(90)
    def test_get_team(self):
        """Test searching for specific team"""
        with BetkingPlaywright(headless=True) as betking:
            data = betking.get_team("Manchester")

            assert isinstance(data, list)
            # Verify matches contain the team name
            for match in data:
                assert "Manchester" in match["match"]

    @pytest.mark.timeout(90)
    def test_manual_browser_management(self):
        """Test manual browser start/stop"""
        betking = BetkingPlaywright(headless=True)

        # Browser should not be started yet
        assert betking.browser is None

        try:
            betking._start_browser()
            assert betking.browser is not None
            assert betking.page is not None

            # Fetch some data
            data = betking.get_league(Betid.PREMIERLEAGUE)
            assert isinstance(data, list)

        finally:
            betking._stop_browser()
            assert betking.browser is None

    def test_non_headless_mode(self):
        """Test that non-headless mode can be initialized"""
        betking = BetkingPlaywright(headless=False)
        assert betking.headless is False
        # Don't actually start browser in non-headless during tests

    def test_custom_timeout(self):
        """Test custom timeout setting"""
        betking = BetkingPlaywright(headless=True, timeout=60000)
        assert betking.timeout == 60000


@pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason="Playwright not installed")
class TestBetkingPlaywrightRequestErrors:
    """get_league must wrap page.request.get() failures as NaijaBetError, offline (no real browser)."""

    class _StubRequest:
        def __init__(self, exc: Exception) -> None:
            self._exc = exc
            self.last_timeout = None

        def get(self, url: str, timeout=None):
            self.last_timeout = timeout
            raise self._exc

    class _StubPage:
        def __init__(self, exc: Exception) -> None:
            self.request = TestBetkingPlaywrightRequestErrors._StubRequest(exc)

    @staticmethod
    def _stubbed_betking(exc: Exception, timeout: int = 30000) -> BetkingPlaywright:
        betking = BetkingPlaywright(headless=True, timeout=timeout)
        # Pretend the browser is already running so get_league() doesn't try to launch one.
        betking.browser = object()
        betking.page = TestBetkingPlaywrightRequestErrors._StubPage(exc)
        return betking

    def test_get_league_wraps_playwright_timeout_error(self):
        betking = self._stubbed_betking(PlaywrightTimeoutError("x"))
        with pytest.raises(BookmakerTimeoutError):
            betking.get_league(Betid.PREMIERLEAGUE)

    def test_get_league_wraps_playwright_error(self):
        betking = self._stubbed_betking(PlaywrightError("boom"))
        with pytest.raises(BookmakerUnreachableError):
            betking.get_league(Betid.PREMIERLEAGUE)

    def test_get_league_forwards_timeout_to_request_get(self):
        betking = self._stubbed_betking(PlaywrightTimeoutError("x"), timeout=5000)
        with pytest.raises(BookmakerTimeoutError):
            betking.get_league(Betid.PREMIERLEAGUE)
        assert betking.page.request.last_timeout == 5000
        assert betking.request_timeout == (5.0, 5.0)


@pytest.mark.skipif(PLAYWRIGHT_AVAILABLE, reason="Only run when Playwright not available")
class TestBetkingPlaywrightNotInstalled:
    """Tests to verify graceful handling when Playwright not installed"""

    def test_import_error_handling(self):
        """Test that missing Playwright is handled gracefully"""
        # This test only runs if Playwright is NOT available
        assert not PLAYWRIGHT_AVAILABLE


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
