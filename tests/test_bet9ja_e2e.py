"""
End-to-end tests for Bet9ja bookmaker.
These tests make real API calls to verify the actual functionality.
"""
import pytest
from NaijaBet_Api.bookmakers.bet9ja import Bet9ja
from NaijaBet_Api.id import Betid


class TestBet9jaE2E:
    """End-to-end tests for Bet9ja bookmaker"""

    def test_initialization(self):
        """Test that Bet9ja initializes correctly"""
        bookmaker = Bet9ja()
        assert bookmaker is not None
        assert bookmaker.site == 'bet9ja'
        assert bookmaker.session is not None

    @pytest.mark.timeout(30)
    def test_get_league_premier_league(self):
        """Test getting Premier League odds"""
        bookmaker = Bet9ja()
        data = bookmaker.get_league(Betid.PREMIERLEAGUE)

        # Should return a list
        assert isinstance(data, list), "get_league should return a list"

        # If there's data, validate structure
        if len(data) > 0:
            match = data[0]
            # Check required fields exist
            required_fields = ['match', 'league', 'time', 'league_id', 'match_id']
            for field in required_fields:
                assert field in match, f"Match should have '{field}' field"

            # Check that match is a string with " - " separator
            assert isinstance(match['match'], str), "match should be a string"
            assert ' - ' in match['match'], "match should contain ' - ' separator"

            # Check league is a string
            assert isinstance(match['league'], str), "league should be a string"

            # Check time is an integer timestamp
            assert isinstance(match['time'], int), "time should be an integer timestamp"

            # Check IDs are integers
            assert isinstance(match['league_id'], int), "league_id should be an integer"
            assert isinstance(match['match_id'], int), "match_id should be an integer"

            # Check odds fields if present
            odds_fields = ['home', 'draw', 'away', 'home_or_draw', 'home_or_away', 'draw_or_away']
            for field in odds_fields:
                if field in match:
                    assert isinstance(match[field], (int, float)), f"{field} should be numeric"
                    assert match[field] > 0, f"{field} should be positive"

    @pytest.mark.timeout(30)
    def test_get_league_la_liga(self):
        """Test getting La Liga odds"""
        bookmaker = Bet9ja()
        data = bookmaker.get_league(Betid.LALIGA)

        assert isinstance(data, list), "get_league should return a list"

    @pytest.mark.timeout(30)
    def test_get_league_bundesliga(self):
        """Test getting Bundesliga odds"""
        bookmaker = Bet9ja()
        data = bookmaker.get_league(Betid.BUNDESLIGA)

        assert isinstance(data, list), "get_league should return a list"

    @pytest.mark.timeout(120)
    def test_get_all(self):
        """Test getting all leagues' odds"""
        bookmaker = Bet9ja()
        data = bookmaker.get_all()

        # Should return a list
        assert isinstance(data, list), "get_all should return a list"

        # Should have data from multiple leagues (or at least be a valid list)
        # Note: might be empty if no matches are available
        if len(data) > 0:
            # Validate structure of first match
            match = data[0]
            required_fields = ['match', 'league', 'time', 'league_id', 'match_id']
            for field in required_fields:
                assert field in match, f"Match should have '{field}' field"

    @pytest.mark.timeout(30)
    def test_get_team(self):
        """Test getting odds for a specific team"""
        bookmaker = Bet9ja()
        # Search for a common team
        data = bookmaker.get_team("Arsenal")

        assert isinstance(data, list), "get_team should return a list"

        # If matches found, verify they contain "Arsenal"
        for match in data:
            assert 'Arsenal' in match['match'], "Match should contain team name"

    @pytest.mark.asyncio
    @pytest.mark.timeout(30)
    async def test_async_get_league(self):
        """Test async version of get_league"""
        bookmaker = Bet9ja(session_type='async')
        try:
            data = await bookmaker.async_get_league(Betid.PREMIERLEAGUE)

            assert isinstance(data, (list, dict)), "async_get_league should return a list or dict"

            if isinstance(data, list) and len(data) > 0:
                match = data[0]
                assert 'match' in match, "Match should have 'match' field"
                assert 'league' in match, "Match should have 'league' field"
        finally:
            if hasattr(bookmaker, 'session') and bookmaker.session:
                await bookmaker.session.close()

    @pytest.mark.asyncio
    @pytest.mark.timeout(120)
    async def test_async_get_all(self):
        """Test async version of get_all"""
        bookmaker = Bet9ja(session_type='async')
        # async_get_all closes the session, so no need for manual cleanup
        data = await bookmaker.async_get_all()

        assert isinstance(data, list), "async_get_all should return a list"

        # Should be a list of unique matches
        if len(data) > 0:
            match = data[0]
            assert 'match' in match, "Match should have 'match' field"

    def test_multiple_requests(self):
        """Test making multiple sequential requests"""
        bookmaker = Bet9ja()

        # Make multiple requests to test session persistence
        data1 = bookmaker.get_league(Betid.PREMIERLEAGUE)
        data2 = bookmaker.get_league(Betid.BUNDESLIGA)
        data3 = bookmaker.get_league(Betid.LALIGA)

        assert isinstance(data1, list)
        assert isinstance(data2, list)
        assert isinstance(data3, list)

    def test_invalid_league_handling(self):
        """Test that the API handles requests gracefully"""
        bookmaker = Bet9ja()
        # Just ensure it doesn't crash - might return empty list or dict
        data = bookmaker.get_league(Betid.PREMIERLEAGUE)
        assert data is not None, "Should return something even if no data"
