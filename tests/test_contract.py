"""Offline contract tests for BookmakerBaseClass: lazy sessions, timeouts, typed failures, the errors ledger."""

import json
import time
from urllib.parse import urlparse

import aiohttp
import pytest
import requests
from urllib3.util import connection as urllib3_connection

import NaijaBet_Api.bookmakers.BaseClass as base_module
from NaijaBet_Api import (
    BookmakerBlockedError,
    BookmakerTimeoutError,
    BookmakerUnreachableError,
    NaijaBetError,
    ResponseParseError,
)
from NaijaBet_Api.exceptions import classify_wall
from NaijaBet_Api.id import Betid

ROW_KEYS = {
    "match",
    "league",
    "time",
    "league_id",
    "match_id",
    "home",
    "draw",
    "away",
    "home_or_draw",
    "home_or_away",
    "draw_or_away",
}
# The Akamai page as sports.bet9ja.com served it on 2026-09-17; the entities are the real encoding.
DENIED_BODY = (
    "<HTML><HEAD>\n"
    "<TITLE>Access Denied</TITLE>\n"
    "</HEAD><BODY>\n"
    "<H1>Access Denied</H1>\n"
    " \n"
    "You don't have permission to access "
    '"http&#58;&#47;&#47;sports&#46;bet9ja&#46;com&#47;desktop&#47;feapi&#47;PalimpsestAjax&#47;GetSports&#63;"'
    " on this server.<P>\n"
    "Reference&#32;&#35;18&#46;b8fd317&#46;1789664171&#46;1360c987\n"
    "<P>https&#58;&#47;&#47;errors&#46;edgesuite&#46;net&#47;18&#46;b8fd317&#46;1789664171&#46;1360c987</P>\n"
    "</BODY>\n"
    "</HTML>\n"
)
CHALLENGE_BODY = "<html><head><title>Just a moment...</title></head><body>cf-mitigated</body></html>"


def test_construct_makes_no_request(stub, httpserver):
    start = time.perf_counter()
    stub()
    elapsed = time.perf_counter() - start
    assert httpserver.log == []
    assert elapsed < 0.05


def test_get_league_returns_eleven_keys(stub, league_routes, httpserver):
    league_routes()
    rows = stub().get_league(Betid.PREMIERLEAGUE)
    assert len(rows) == 3
    for row in rows:
        assert set(row) == ROW_KEYS
        for key in ("home", "draw", "away", "home_or_draw", "home_or_away", "draw_or_away"):
            assert isinstance(row[key], float)
        assert isinstance(row["league_id"], int)
        assert isinstance(row["match_id"], int)
        assert isinstance(row["time"], int)
    paths = [req.path for req, _ in httpserver.log]
    assert paths[0] == "/"
    assert paths[1].startswith("/league/")


def test_403_denied(stub, league_routes, league_log):
    league_routes(status=403, body=DENIED_BODY)
    with pytest.raises(BookmakerBlockedError) as info:
        stub().get_league()
    assert info.value.status == 403
    assert info.value.wall == "denied"
    assert isinstance(info.value.__cause__, requests.HTTPError)
    assert "Access Denied" in info.value.body_excerpt
    assert len(league_log()) == 1


def test_503_challenge(stub, league_routes, league_log):
    league_routes(status=503, body=CHALLENGE_BODY)
    with pytest.raises(BookmakerBlockedError) as info:
        stub().get_league()
    assert info.value.wall == "challenge"
    assert len(league_log()) == 1


def test_unreachable_closed_port(stub, point_at, closed_port, no_retry_sleep, monkeypatch):
    point_at(closed_port)
    port = urlparse(closed_port).port
    attempts = []
    real_create = urllib3_connection.create_connection

    def counting_create(address, *args, **kwargs):
        if address[1] == port:
            attempts.append(address)
        return real_create(address, *args, **kwargs)

    monkeypatch.setattr(urllib3_connection, "create_connection", counting_create)
    with pytest.raises(BookmakerUnreachableError) as info:
        stub().get_league()
    assert isinstance(info.value.__cause__, requests.ConnectionError)
    assert len(attempts) == 2
    assert no_retry_sleep[0] == [1.0]


def test_connect_timeout_retries_then_succeeds(stub, league_routes, no_retry_sleep):
    league_routes()
    bookmaker = stub()
    bookmaker._warmed["sync"] = True
    real_get = bookmaker.session.get
    calls = []

    def flaky_get(url, *args, **kwargs):
        calls.append(url)
        if len(calls) == 1:
            raise requests.exceptions.ConnectTimeout("connect timed out")
        return real_get(url, *args, **kwargs)

    bookmaker.session.get = flaky_get
    rows = bookmaker.get_league()
    assert len(rows) == 3
    assert len(calls) == 2
    assert no_retry_sleep[0] == [1.0]


def test_connect_timeout_twice_raises_unreachable(stub, league_routes, no_retry_sleep):
    league_routes()
    bookmaker = stub()
    bookmaker._warmed["sync"] = True

    def always_connect_timeout(url, *args, **kwargs):
        raise requests.exceptions.ConnectTimeout("connect timed out")

    bookmaker.session.get = always_connect_timeout
    with pytest.raises(BookmakerUnreachableError) as info:
        bookmaker.get_league()
    assert not isinstance(info.value, BookmakerTimeoutError)
    assert no_retry_sleep[0] == [1.0]


def test_timeout_short_sync(stub, point_at, blackhole):
    point_at(blackhole)
    start = time.perf_counter()
    with pytest.raises(BookmakerTimeoutError) as info:
        stub(timeout=(1, 2)).get_league()
    elapsed = time.perf_counter() - start
    assert isinstance(info.value, TimeoutError)
    assert isinstance(info.value, BookmakerUnreachableError)
    assert 2 <= elapsed < 5


async def test_timeout_short_async(stub, point_at, blackhole):
    point_at(blackhole)
    bookmaker = stub(timeout=(1, 2))
    start = time.perf_counter()
    try:
        with pytest.raises(BookmakerTimeoutError) as info:
            await bookmaker.async_get_league()
    finally:
        await bookmaker.aclose()
    elapsed = time.perf_counter() - start
    assert isinstance(info.value, TimeoutError)
    assert 2 <= elapsed < 5


@pytest.mark.timeout(60)
def test_timeout_default_sync(stub, point_at, blackhole):
    point_at(blackhole)
    start = time.perf_counter()
    with pytest.raises(BookmakerTimeoutError):
        stub().get_league()
    assert 30 <= time.perf_counter() - start < 45


@pytest.mark.timeout(60)
async def test_timeout_default_async(stub, point_at, blackhole):
    point_at(blackhole)
    bookmaker = stub()
    start = time.perf_counter()
    try:
        with pytest.raises(BookmakerTimeoutError):
            await bookmaker.async_get_league()
    finally:
        await bookmaker.aclose()
    assert 30 <= time.perf_counter() - start < 45


def test_parse_error_not_json(stub, league_routes):
    league_routes(body="<html>not json</html>")
    with pytest.raises(ResponseParseError) as info:
        stub().get_league()
    assert isinstance(info.value.__cause__, json.JSONDecodeError)


def test_parse_error_missing_path(stub, league_routes):
    league_routes(body=json.dumps({"foo": 1}))
    with pytest.raises(ResponseParseError):
        stub().get_league()


def test_empty_events_returns_empty_list(stub, league_routes):
    league_routes(body=json.dumps({"D": {"E": []}}))
    assert stub().get_league() == []


async def test_async_get_all_one_session(stub, league_routes, league_log, monkeypatch):
    league_routes()
    constructions = []
    real_init = aiohttp.ClientSession.__init__

    def counting_init(self, *args, **kwargs):
        constructions.append(self)
        real_init(self, *args, **kwargs)

    monkeypatch.setattr(aiohttp.ClientSession, "__init__", counting_init)
    bookmaker = stub()
    rows = await bookmaker.async_get_all()
    assert len(rows) == 3 * len(Betid)
    assert bookmaker.errors == {}
    assert len(constructions) == 1
    assert len(league_log()) == len(Betid)
    assert bookmaker.async_session.closed is False
    await bookmaker.aclose()
    assert constructions[0].closed is True


async def test_async_get_all_warms_once(stub, league_routes, httpserver):
    """PERF-1 regression: the ten concurrent league tasks must share one warm-up GET."""
    league_routes()
    bookmaker = stub()
    try:
        rows = await bookmaker.async_get_all()
        assert len(rows) == 3 * len(Betid)
        home_requests = [req for req, _ in httpserver.log if req.path == "/"]
        assert len(home_requests) == 1
    finally:
        await bookmaker.aclose()


async def test_caller_session_not_closed(stub, league_routes):
    league_routes()
    own = aiohttp.ClientSession()
    try:
        rows = await stub().async_get_league(Betid.PREMIERLEAGUE, async_session=own)
        assert len(rows) == 3
        assert own.closed is False
    finally:
        await own.close()


async def test_same_instance_both_transports(stub, league_routes):
    league_routes()
    bookmaker = stub()
    assert len(bookmaker.get_league()) == 3
    session_before = bookmaker.session
    try:
        assert len(await bookmaker.async_get_league()) == 3
    finally:
        await bookmaker.aclose()
    assert len(bookmaker.get_league()) == 3
    assert bookmaker.session is session_before


def test_retry_500_into_ledger(stub, league_routes, league_log, no_retry_sleep):
    failing = Betid.PREMIERLEAGUE
    others = [league for league in Betid if league is not failing]
    league_routes(leagues=others)
    league_routes(leagues=[failing], sequence=[(500, "boom"), (500, "boom")])
    bookmaker = stub()
    rows = bookmaker.get_all()
    assert len(rows) == 3 * len(others)
    assert set(bookmaker.errors) == {failing}
    error = bookmaker.errors[failing]
    assert isinstance(error, BookmakerBlockedError)
    assert error.status == 500
    assert error.wall == "http"
    failing_requests = [req for req in league_log() if req.path == f"/league/{failing.bet9ja_id}"]
    assert len(failing_requests) == 2
    assert no_retry_sleep[0] == [1.0]


def test_all_fail_raises(stub, league_routes, no_retry_sleep):
    league_routes(status=500, body="boom")
    bookmaker = stub()
    with pytest.raises(NaijaBetError):
        bookmaker.get_all()
    assert len(bookmaker.errors) == len(Betid)


def test_get_all_fans_out_leagues(stub, league_routes, httpserver):
    """PERF-2 regression: get_all() fans the ten leagues out instead of retrying them one after
    another, so the retry sleeps overlap instead of stacking up."""
    league_routes(status=500, body="boom")
    bookmaker = stub()
    start = time.perf_counter()
    with pytest.raises(NaijaBetError):
        bookmaker.get_all()
    elapsed = time.perf_counter() - start
    assert elapsed < 4.0  # sequential retries need at least 10 * 1.0 s
    assert len(bookmaker.errors) == len(Betid)
    home_requests = [req for req, _ in httpserver.log if req.path == "/"]
    assert len(home_requests) == 1


async def test_async_get_league_parses_off_loop(stub, league_routes, monkeypatch):
    """PERF-3 regression: the async path offloads ``_parse`` to a worker thread via ``asyncio.to_thread``."""
    league_routes()
    calls = []
    real_to_thread = base_module.asyncio.to_thread

    async def counting_to_thread(func, *args, **kwargs):
        calls.append((func, args, kwargs))
        return await real_to_thread(func, *args, **kwargs)

    monkeypatch.setattr(base_module.asyncio, "to_thread", counting_to_thread)
    bookmaker = stub()
    try:
        rows = await bookmaker.async_get_league(Betid.PREMIERLEAGUE)
    finally:
        await bookmaker.aclose()
    assert len(calls) == 1
    assert len(rows) == 3


async def test_all_fail_raises_async(stub, league_routes, no_retry_sleep):
    league_routes(status=500, body="boom")
    bookmaker = stub()
    try:
        with pytest.raises(NaijaBetError):
            await bookmaker.async_get_all()
    finally:
        await bookmaker.aclose()
    assert len(bookmaker.errors) == len(Betid)
    assert no_retry_sleep[1] == [1.0] * len(Betid)


def test_retry_counts(stub, league_routes, league_log, bet9ja_payload, no_retry_sleep):
    league_routes(sequence=[(500, "boom"), (200, json.dumps(bet9ja_payload))])
    assert len(stub().get_league()) == 3
    assert len(league_log()) == 2


def test_no_retry_on_403(stub, league_routes, league_log, no_retry_sleep):
    league_routes(status=403, body="nope")
    with pytest.raises(BookmakerBlockedError) as info:
        stub().get_league()
    assert info.value.wall == "http"
    assert len(league_log()) == 1
    assert no_retry_sleep[0] == []


def test_session_type_deprecated(stub, league_routes):
    league_routes()
    with pytest.warns(DeprecationWarning, match="session_type"):
        bookmaker = stub(session_type="async")
    assert len(bookmaker.get_league()) == 3


def test_brotli_route_serves_encoded_bytes(httpserver, brotli_body):
    httpserver.expect_request("/br").respond_with_data(brotli_body, headers={"Content-Encoding": "br"})
    raw = requests.get(httpserver.url_for("/br"), headers={"Accept-Encoding": "identity"}, timeout=5)
    assert raw.headers["Content-Encoding"] == "br"
    assert raw.status_code == 200


async def test_closed_caller_session_is_unreachable(stub, league_routes):
    league_routes()
    closed = aiohttp.ClientSession()
    await closed.close()
    with pytest.raises(BookmakerUnreachableError) as info:
        await stub().async_get_league(async_session=closed)
    assert isinstance(info.value.__cause__, RuntimeError)
    assert "closed" in str(info.value)


async def test_unreachable_closed_port_async(stub, point_at, closed_port, no_retry_sleep):
    point_at(closed_port)
    bookmaker = stub()
    try:
        with pytest.raises(BookmakerUnreachableError) as info:
            await bookmaker.async_get_league()
    finally:
        await bookmaker.aclose()
    assert isinstance(info.value.__cause__, aiohttp.ClientConnectionError)
    assert no_retry_sleep[1] == [1.0]


def test_close_resets_blocking_session(stub, league_routes):
    league_routes()
    bookmaker = stub()
    bookmaker.get_league()
    first = bookmaker.session
    bookmaker.close()
    assert bookmaker.get_league()
    assert bookmaker.session is not first


def test_get_team_filters_rows(stub, league_routes):
    league_routes()
    rows = stub().get_team("arsenal")
    assert len(rows) == len(Betid)
    assert all("Arsenal" in row["match"] for row in rows)


def test_normalizer_error_becomes_parse_error(stub, league_routes):
    league_routes()

    class Broken(stub):
        def normalizer(self, data):
            raise KeyError("D")

    with pytest.raises(ResponseParseError) as info:
        Broken().get_league()
    assert isinstance(info.value.__cause__, KeyError)


async def test_warm_up_failure_does_not_block_fetch(stub, league_routes, closed_port):
    league_routes()

    class ColdRoot(stub):
        _url = closed_port

    bookmaker = ColdRoot()
    assert len(bookmaker.get_league()) == 3
    try:
        assert len(await bookmaker.async_get_league()) == 3
    finally:
        await bookmaker.aclose()


def test_classify_wall_decodes_entities():
    assert classify_wall(403, DENIED_BODY) == "denied"
    assert classify_wall(403, CHALLENGE_BODY) == "challenge"
    assert classify_wall(502, "bad gateway") == "http"
