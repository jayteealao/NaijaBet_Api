"""The one assertion the live gate makes: a bookmaker returns rows and nothing blocked it.

The suite runs under the ``live_site`` marker from a Nigerian egress; ``LIVE_EXPECT`` narrows the
bookmakers that can fail the run.
"""

from __future__ import annotations

import os

from NaijaBet_Api.exceptions import BookmakerBlockedError, NaijaBetError
from NaijaBet_Api.id import Betid

BOOKMAKERS = ("bet9ja", "betking", "nairabet")

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


def expected_bookmakers() -> frozenset[str]:
    """The bookmakers this run must prove, from ``LIVE_EXPECT`` (comma-separated); all three by default.

    A bookmaker outside the set is still driven, and its outcome is reported, but it cannot fail the run.
    """
    raw = os.environ.get("LIVE_EXPECT", ",".join(BOOKMAKERS))
    names = frozenset(name.strip() for name in raw.split(",") if name.strip())
    unknown = names - set(BOOKMAKERS)
    if unknown:
        raise ValueError(f"LIVE_EXPECT names unknown bookmakers: {sorted(unknown)}")
    return names


def check_rows(site: str, rows: list[dict], errors: dict[Betid, NaijaBetError]) -> int:
    """Return the row count, or fail.

    Fails when any league was blocked (an egress fault, not an empty fixture list) or when the
    union across the ten leagues is empty. Out-of-season leagues return no rows and no error.
    """
    blocked = {league.name: err for league, err in errors.items() if isinstance(err, BookmakerBlockedError)}
    assert not blocked, f"{site}: blocked on {sorted(blocked)}: {blocked}"
    assert rows, f"{site}: zero rows across {len(Betid)} leagues; errors={errors}"
    missing = ROW_KEYS - set(rows[0])
    assert not missing, f"{site}: first row lacks {sorted(missing)}"
    return len(rows)


def assert_live_rows(bookmaker) -> int:
    """Call ``get_all`` and return the row count; see :func:`check_rows` for the failure rule."""
    return check_rows(bookmaker.site, bookmaker.get_all(), bookmaker.errors)


def collect(bookmaker) -> tuple[list[dict], dict[Betid, NaijaBetError]]:
    """``get_all`` for a bookmaker outside the expected set: the all-leagues-failed raise folds into the ledger."""
    try:
        rows = bookmaker.get_all()
    except NaijaBetError:
        rows = []
    return rows, bookmaker.errors


def report_blocked(site: str, errors: dict[Betid, NaijaBetError]) -> dict:
    """The block a bookmaker outside the expected set met: status, wall, and the leagues it covered."""
    blocked = [(league.name, err) for league, err in errors.items() if isinstance(err, BookmakerBlockedError)]
    first = blocked[0][1] if blocked else None
    return {
        "status": first.status if first else None,
        "wall": first.wall if first else None,
        "leagues": sorted(name for name, _ in blocked),
    }


async def async_collect(bookmaker, session) -> tuple[list[dict], dict[Betid, NaijaBetError]]:
    """Drive the ten leagues through ``async_get_league`` on a caller session; return rows and the error ledger."""
    rows: list[dict] = []
    errors: dict[Betid, NaijaBetError] = {}
    for league in Betid:
        try:
            rows += await bookmaker.async_get_league(league, async_session=session)
        except NaijaBetError as exc:
            errors[league] = exc
    return rows, errors
