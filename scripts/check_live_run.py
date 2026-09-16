"""Validate a ``live-run.json`` before the release accepts it as the live-gate override.

Usage: ``python scripts/check_live_run.py live-run.json`` or ``... -`` to read stdin.
Exit 0 when the record is at most 7 days old, names all three bookmakers with row counts above
zero, records a passing run, and carries the git sha; exit 1 with the first failing reason.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone

MAX_AGE = timedelta(days=7)
BOOKMAKERS = ("bet9ja", "betking", "nairabet")


def check(record: dict, now: datetime) -> str | None:
    """Return the first reason the record is unacceptable, or None."""
    try:
        ran_at = datetime.fromisoformat(str(record.get("ran-at")))
    except ValueError:
        return f"ran-at {record.get('ran-at')!r} is not an ISO 8601 timestamp"
    if ran_at.tzinfo is None:
        return "ran-at carries no timezone; the record must be written in UTC"
    age = now - ran_at
    if age > MAX_AGE:
        return f"live-run.json is {age.days} days old; the override accepts at most {MAX_AGE.days}"
    counts = record.get("bookmakers")
    if not isinstance(counts, dict):
        return "bookmakers is missing"
    for name in BOOKMAKERS:
        count = counts.get(name)
        if count is None:
            return f"bookmakers lacks {name}"
        if not isinstance(count, int) or isinstance(count, bool) or count <= 0:
            return f"bookmakers.{name} is {count!r}; an integer above zero is required"
    if record.get("passed") is not True:
        return "passed is not true; the recorded run did not pass"
    if not record.get("git-sha"):
        return "git-sha is missing"
    return None


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: check_live_run.py <live-run.json | ->", file=sys.stderr)
        return 2
    if argv[1] == "-":
        text = sys.stdin.read()
    else:
        with open(argv[1], encoding="utf-8") as handle:
            text = handle.read()
    try:
        record = json.loads(text)
    except json.JSONDecodeError as exc:
        print(f"live-run.json is not valid JSON: {exc}", file=sys.stderr)
        return 1
    reason = check(record, datetime.now(timezone.utc))
    if reason:
        print(reason, file=sys.stderr)
        return 1
    counts = ", ".join(f"{name}={record['bookmakers'][name]}" for name in BOOKMAKERS)
    print(f"live-run.json accepted: ran-at {record['ran-at']}, {counts}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
