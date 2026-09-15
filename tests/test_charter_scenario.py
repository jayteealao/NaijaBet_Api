"""The core loop end to end, as a user drives it, against the local stub.

Steps 1 to 6 of the charter scenario: construct offline, fetch rows, receive a denied
block, run ten leagues on one session, see one league retried into the error ledger,
and get a timeout raised within its bound.
"""

import json
import time

import pytest

from NaijaBet_Api import BookmakerBlockedError, BookmakerTimeoutError
from NaijaBet_Api.id import Betid

DENIED_BODY = "Access Denied. You don't have permission to access this page. Reference #18.6f1"


async def test_charter_steps_1_to_6(stub, league_routes, league_log, httpserver, point_at, blackhole, no_retry_sleep):
    # Step 1 — construct offline.
    bookmaker = stub()
    assert httpserver.log == [], "step 1: construction made a request"

    # Step 2 — fetch rows for one league.
    healthy = [league for league in Betid if league not in (Betid.PREMIERLEAGUE, Betid.LALIGA)]
    league_routes(leagues=healthy)
    rows = bookmaker.get_league(healthy[0])
    assert len(rows) == 3 and "home" in rows[0], "step 2: no rows returned"

    # Step 3 — a denied block is a typed exception.
    league_routes(leagues=[Betid.PREMIERLEAGUE], status=403, body=DENIED_BODY)
    with pytest.raises(BookmakerBlockedError) as blocked:
        bookmaker.get_league(Betid.PREMIERLEAGUE)
    assert (blocked.value.status, blocked.value.wall) == (403, "denied"), "step 3: wrong block classification"

    # Step 4 and 5 — ten leagues on one session; one league retried into the ledger.
    league_routes(leagues=[Betid.LALIGA], sequence=[(500, "boom"), (500, "boom")])
    httpserver.clear_log()
    all_rows = await bookmaker.async_get_all()
    try:
        assert len(all_rows) == 3 * len(healthy), "step 4: union of healthy leagues has the wrong size"
        assert set(bookmaker.errors) == {Betid.PREMIERLEAGUE, Betid.LALIGA}, "step 5: ledger has the wrong keys"
        assert bookmaker.errors[Betid.LALIGA].status == 500, "step 5: retried league not recorded as 500"
        laliga_requests = [r for r in league_log() if r.path == f"/league/{Betid.LALIGA.bet9ja_id}"]
        assert len(laliga_requests) == 2, "step 5: the 500 league was not retried exactly once"
        assert no_retry_sleep[1] == [1.0], "step 5: retry delay not observed"
        assert bookmaker.async_session.closed is False, "step 4: the shared session was closed"
    finally:
        await bookmaker.aclose()

    # Step 6 — a timeout is raised inside its bound.
    point_at(blackhole)
    slow = stub(timeout=(1, 2))
    start = time.perf_counter()
    with pytest.raises(BookmakerTimeoutError) as timed_out:
        slow.get_league(Betid.PREMIERLEAGUE)
    elapsed = time.perf_counter() - start
    assert isinstance(timed_out.value, TimeoutError), "step 6: not a TimeoutError"
    assert 2 <= elapsed < 5, f"step 6: timeout took {elapsed:.1f} s"
    assert json.loads(json.dumps(all_rows[0]))["league"] == "Premier League", "step 2: row is not JSON-serialisable"
