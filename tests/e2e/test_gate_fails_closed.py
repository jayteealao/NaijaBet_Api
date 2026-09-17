"""The live assertion fails on zero rows and on a block; the expected set narrows only through LIVE_EXPECT."""

import subprocess
import sys
from pathlib import Path

import pytest

from NaijaBet_Api.bookmakers import Bet9ja, Betking
from NaijaBet_Api.exceptions import BookmakerBlockedError, NaijaBetError
from NaijaBet_Api.id import Betid
from tests.e2e.gate import BOOKMAKERS, assert_live_rows, async_collect, collect, expected_bookmakers, report_blocked

REPO = Path(__file__).resolve().parent.parent.parent
ROW = {key: 1.5 for key in ("home", "draw", "away", "home_or_draw", "home_or_away", "draw_or_away")}
ROW.update({"match": "A - B", "league": "L", "time": 0, "league_id": 1, "match_id": 1})


def test_zero_rows_fail_and_name_the_bookmaker(monkeypatch):
    monkeypatch.setattr(Bet9ja, "get_league", lambda self, league=Betid.PREMIERLEAGUE: [])

    with pytest.raises(AssertionError, match="bet9ja: zero rows across 10 leagues"):
        assert_live_rows(Bet9ja())


def test_one_blocked_league_fails_and_names_the_league(monkeypatch):
    def get_league(self, league=Betid.PREMIERLEAGUE):
        if league is Betid.PREMIERLEAGUE:
            raise BookmakerBlockedError("betking", 403, "denied")
        return [dict(ROW)]

    monkeypatch.setattr(Betking, "get_league", get_league)

    with pytest.raises(AssertionError, match=r"betking: blocked on \['PREMIERLEAGUE'\]"):
        assert_live_rows(Betking())


def test_rows_pass_and_return_the_count(monkeypatch):
    monkeypatch.setattr(Bet9ja, "get_league", lambda self, league=Betid.PREMIERLEAGUE: [dict(ROW)])

    assert assert_live_rows(Bet9ja()) == 10


def test_default_run_collects_no_live_tests():
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/e2e", "--collect-only", "-q", "-p", "no:cacheprovider"],
        capture_output=True,
        text=True,
        cwd=REPO,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "test_live_rows" not in result.stdout, result.stdout
    assert "deselected" in result.stdout, result.stdout


def test_expected_defaults_to_all_three(monkeypatch):
    monkeypatch.delenv("LIVE_EXPECT", raising=False)

    assert expected_bookmakers() == frozenset(BOOKMAKERS)


def test_expected_narrows_from_env(monkeypatch):
    monkeypatch.setenv("LIVE_EXPECT", "betking,nairabet")

    assert expected_bookmakers() == {"betking", "nairabet"}


def test_unknown_expected_name_raises(monkeypatch):
    monkeypatch.setenv("LIVE_EXPECT", "bet9ja,sportybet")

    with pytest.raises(ValueError, match="sportybet"):
        expected_bookmakers()


def test_blocked_bookmaker_is_reported_and_still_fails_the_assertion(monkeypatch):
    def get_league(self, league=Betid.PREMIERLEAGUE):
        raise BookmakerBlockedError("bet9ja", 403, "denied")

    monkeypatch.setattr(Bet9ja, "get_league", get_league)

    rows, errors = collect(Bet9ja())

    assert rows == []
    assert report_blocked("bet9ja", errors) == {
        "status": 403,
        "wall": "denied",
        "leagues": sorted(league.name for league in Betid),
    }
    with pytest.raises(NaijaBetError, match="all 10 leagues failed"):
        assert_live_rows(Bet9ja())


async def test_async_collect_gathers_rows_and_errors(monkeypatch):
    async def async_get_league(self, league=Betid.PREMIERLEAGUE, async_session=None):
        if league is Betid.PREMIERLEAGUE:
            raise BookmakerBlockedError("betking", 403, "challenge")
        return [dict(ROW)]

    monkeypatch.setattr(Betking, "async_get_league", async_get_league)

    rows, errors = await async_collect(Betking(), session=object())

    assert len(rows) == len(Betid) - 1
    assert report_blocked("betking", errors) == {"status": 403, "wall": "challenge", "leagues": ["PREMIERLEAGUE"]}
