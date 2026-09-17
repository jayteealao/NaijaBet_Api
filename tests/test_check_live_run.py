"""The override checker accepts a fresh passing record and rejects a stale or incomplete one."""

import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "scripts" / "check_live_run.py"
sys.path.insert(0, str(REPO / "scripts"))

from check_live_run import check  # noqa: E402

NOW = datetime(2026, 9, 16, 12, 0, tzinfo=timezone.utc)


def record(days_old: float, **overrides) -> dict:
    base = {
        "ran-at": (NOW - timedelta(days=days_old)).isoformat(timespec="seconds"),
        "egress": {"ip": "79.127.149.13", "city": "Lagos", "country": "NG", "org": "Datacamp Limited"},
        "bookmakers": {"bet9ja": 118, "betking": 118, "nairabet": 118},
        "git-sha": "0bad3fffa3d3cc3be96ac7ab6b514459afefdf00",
        "passed": True,
    }
    base.update(overrides)
    return base


def test_two_day_record_is_accepted():
    assert check(record(2), NOW) is None


def test_eight_day_record_is_rejected_with_its_age():
    assert check(record(8), NOW) == "live-run.json is 8 days old; the override accepts at most 7"


def test_future_record_is_rejected():
    assert check(record(-1 / 24), NOW) == "ran-at is in the future"


def test_one_minute_ago_record_is_accepted():
    assert check(record(1 / 1440), NOW) is None


def test_missing_bookmaker_is_named():
    assert check(record(1, bookmakers={"bet9ja": 118, "nairabet": 118}), NOW) == "bookmakers lacks betking"


@pytest.mark.parametrize("count", [0, -1, "118", True])
def test_non_positive_count_is_rejected(count):
    reason = check(record(1, bookmakers={"bet9ja": 118, "betking": count, "nairabet": 118}), NOW)

    assert reason == f"bookmakers.betking is {count!r}; an integer above zero is required"


def test_failed_run_is_rejected():
    assert check(record(1, passed=False), NOW) == "passed is not true; the recorded run did not pass"


def test_naive_timestamp_is_rejected():
    assert "timezone" in check(record(1, **{"ran-at": "2026-09-16T10:00:00"}), NOW)


def test_matching_git_sha_is_accepted():
    assert check(record(1), NOW, "0bad3fffa3d3cc3be96ac7ab6b514459afefdf00") is None


def test_mismatched_git_sha_is_rejected():
    reason = check(record(1), NOW, "ffffffffffffffffffffffffffffffffffffffff")

    assert reason == (
        "git-sha 0bad3fffa3d3cc3be96ac7ab6b514459afefdf00 does not match the released commit "
        "ffffffffffffffffffffffffffffffffffffffff"
    )


def test_short_expected_sha_matches_by_prefix():
    assert check(record(1), NOW, "0bad3ff") is None


def test_short_recorded_sha_matches_by_prefix():
    short = record(1, **{"git-sha": "0bad3ff"})

    assert check(short, NOW, "0bad3fffa3d3cc3be96ac7ab6b514459afefdf00") is None


def test_cli_reads_stdin_and_a_path(tmp_path):
    fresh = record(0)
    fresh["ran-at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    accepted = subprocess.run(
        [sys.executable, str(SCRIPT), "-"], input=json.dumps(fresh), capture_output=True, text=True, cwd=REPO
    )
    stale = tmp_path / "stale.json"
    stale.write_text(json.dumps(record(8)), encoding="utf-8")
    rejected = subprocess.run([sys.executable, str(SCRIPT), str(stale)], capture_output=True, text=True, cwd=REPO)

    assert accepted.returncode == 0 and accepted.stdout.startswith("live-run.json accepted: ran-at ")
    assert rejected.returncode == 1 and "days old" in rejected.stderr


def test_cli_rejects_a_mismatched_expected_sha():
    fresh = record(0)
    fresh["ran-at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "-", "ffffffffffffffffffffffffffffffffffffffff"],
        input=json.dumps(fresh),
        capture_output=True,
        text=True,
        cwd=REPO,
    )

    assert result.returncode == 1
    assert "does not match the released commit" in result.stderr
