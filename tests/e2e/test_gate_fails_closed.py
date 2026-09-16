"""The live assertion fails on zero rows and on a block, and the default run selects no live test."""

import subprocess
import sys
from pathlib import Path

import pytest

from NaijaBet_Api.bookmakers import Bet9ja, Betking
from NaijaBet_Api.exceptions import BookmakerBlockedError
from NaijaBet_Api.id import Betid
from tests.e2e.gate import assert_live_rows

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
