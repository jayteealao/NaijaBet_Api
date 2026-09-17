"""BetkingPlaywright.get_all() must run get_league() serially on the calling thread.

Regression test for RUNTIME-1: BetkingPlaywright inherits BookmakerBaseClass.get_all,
which fans get_league out across a concurrent.futures.ThreadPoolExecutor (since commit
db3b535). Sync Playwright binds its driver to the thread that started it, so a call from
a worker thread raises ``greenlet.error: Cannot switch to a different thread`` (source:
playwright/sync_api/_generated.py). This test never drives a real page -- constructing
BetkingPlaywright does not launch a browser (that only happens in _start_browser()) -- it
only asserts that every get_league() call lands on the thread that called get_all().
"""

import threading

from NaijaBet_Api.bookmakers.betking_playwright import BetkingPlaywright
from NaijaBet_Api.id import Betid

ROW = {key: 1.5 for key in ("home", "draw", "away", "home_or_draw", "home_or_away", "draw_or_away")}
ROW.update({"match": "A - B", "league": "L", "time": 0, "league_id": 1, "match_id": 1})


def test_get_all_runs_get_league_serially_on_calling_thread(monkeypatch):
    main_thread_ident = threading.get_ident()
    recorded_idents: list[int] = []

    def fake_get_league(self, league: Betid = Betid.PREMIERLEAGUE):
        recorded_idents.append(threading.get_ident())
        return [dict(ROW)]

    monkeypatch.setattr(BetkingPlaywright, "get_league", fake_get_league)

    # __init__ never starts a browser (only _start_browser() does), so this is safe offline.
    betking = BetkingPlaywright(headless=True)
    rows = betking.get_all()

    assert len(recorded_idents) == len(Betid)
    assert all(ident == main_thread_ident for ident in recorded_idents), recorded_idents
    assert len(rows) == len(Betid)
