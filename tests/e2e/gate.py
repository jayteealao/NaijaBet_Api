"""The one assertion the live gate makes: a bookmaker returns rows and nothing blocked it."""

from __future__ import annotations

from NaijaBet_Api.exceptions import BookmakerBlockedError
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


def assert_live_rows(bookmaker) -> int:
    """Call ``get_all`` and return the row count.

    Fails when any league was blocked (an egress fault, not an empty fixture list) or when the
    union across the ten leagues is empty. Out-of-season leagues return no rows and no error.
    """
    rows = bookmaker.get_all()
    blocked = {league.name: err for league, err in bookmaker.errors.items() if isinstance(err, BookmakerBlockedError)}
    assert not blocked, f"{bookmaker.site}: blocked on {sorted(blocked)}: {blocked}"
    assert rows, f"{bookmaker.site}: zero rows across {len(Betid)} leagues; errors={bookmaker.errors}"
    missing = ROW_KEYS - set(rows[0])
    assert not missing, f"{bookmaker.site}: first row lacks {sorted(missing)}"
    return len(rows)
