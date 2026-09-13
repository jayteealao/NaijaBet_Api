"""
Offline tests for the isinstance-based session-type guards in BookmakerBaseClass.

get_league(), async_get_league() and async_get_all() each check the *actual*
runtime type of self.session before deciding how to proceed, independent of the
session_type the instance was constructed with. No prior test constructed one
session_type and then called the other mode's method, so the mismatch branches
were never exercised. These tests do that, with no real network access.
"""

import requests

from NaijaBet_Api.bookmakers.BaseClass import BookmakerBaseClass
from NaijaBet_Api.id import Betid


class _FakeResponse:
    status_code = 200

    def json(self):
        return {}


class _StubBookmaker(BookmakerBaseClass):
    _site = "bet9ja"
    _url = "https://example.invalid/stub"
    _headers = {}

    def normalizer(self, data):
        return data


async def test_async_get_league_returns_empty_dict_for_blocking_session(monkeypatch):
    """When session_type='blocking' gives self.session a requests.Session, calling
    async_get_league() should hit the aiohttp.ClientSession isinstance guard and
    return {} rather than raise."""
    monkeypatch.setattr(requests.Session, "get", lambda self, *args, **kwargs: _FakeResponse())

    bookmaker = _StubBookmaker(session_type="blocking")
    # Pretend launch_async already ran so it isn't invoked here: launch_async would
    # otherwise overwrite self.session with a real aiohttp.ClientSession and attempt
    # a real network call, masking the very mismatch this test exercises.
    bookmaker.launched = True

    result = await bookmaker.async_get_league(Betid.PREMIERLEAGUE)

    assert result == {}


async def test_async_get_all_returns_list_for_blocking_session(monkeypatch):
    """async_get_all() should tolerate a blocking (requests.Session) session and
    still return a list/dict, since every per-league call hits the same guard."""
    monkeypatch.setattr(requests.Session, "get", lambda self, *args, **kwargs: _FakeResponse())

    bookmaker = _StubBookmaker(session_type="blocking")
    bookmaker.launched = True

    result = await bookmaker.async_get_all()

    assert isinstance(result, (list, dict))


def test_get_league_returns_empty_list_for_async_session():
    """When session_type='async' leaves self.session as something other than a
    requests.Session (its default, None, since launch_async was never awaited),
    calling get_league() should hit the requests.Session isinstance guard and
    return [] rather than raise."""
    bookmaker = _StubBookmaker(session_type="async")

    result = bookmaker.get_league(Betid.PREMIERLEAGUE)

    assert result == []
