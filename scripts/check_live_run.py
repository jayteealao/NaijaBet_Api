"""Validate a ``live-run.json`` before the release accepts it as the live-gate override.

Usage: ``python scripts/check_live_run.py live-run.json [expected-git-sha]`` or ``... -`` to
read stdin. Exit 0 when the record is at most 7 days old, names all three bookmakers with row
counts above zero, carries no ``egress-error`` and a Nigerian egress (``egress.country ==
"NG"``), was not run through a proxy (``proxy-in-use`` is not true), was not narrowed through
``LIVE_EXPECT`` (its ``expected`` list, when present, covers all three), records a passing run,
and carries the git sha; exit 1 with the first failing reason. When ``expected-git-sha`` is
given, the record's ``git-sha`` must also match it (a full match, or a prefix match when one of
the two is a short sha of at least 7 characters); without it, only the presence of ``git-sha``
is checked.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone

MAX_AGE = timedelta(days=7)
BOOKMAKERS = ("bet9ja", "betking", "nairabet")


def _sha_matches(recorded: str, expected: str) -> bool:
    """True when the shas are identical, or one is a >=7-char prefix of the other."""
    if recorded == expected:
        return True
    if len(recorded) >= 7 and expected.startswith(recorded):
        return True
    if len(expected) >= 7 and recorded.startswith(expected):
        return True
    return False


def check(record: dict, now: datetime, expected_sha: str | None = None) -> str | None:
    """Return the first reason the record is unacceptable, or None."""
    try:
        ran_at = datetime.fromisoformat(str(record.get("ran-at")))
    except ValueError:
        return f"ran-at {record.get('ran-at')!r} is not an ISO 8601 timestamp"
    if ran_at.tzinfo is None:
        return "ran-at carries no timezone; the record must be written in UTC"
    if ran_at > now:
        return "ran-at is in the future"
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
    if "egress-error" in record:
        return f"egress-error {record['egress-error']!r}; the run could not prove its egress"
    egress = record.get("egress")
    if not isinstance(egress, dict):
        return "egress is missing"
    country = egress.get("country")
    if country != "NG":
        return f"egress.country is {country!r}; the override needs a Nigerian egress"
    if record.get("proxy-in-use") is True:
        return "proxy-in-use is true; a proxied run cannot serve as the release override"
    expected = record.get("expected")
    if expected is not None:
        if not isinstance(expected, list):
            return "expected is not a list"
        for name in BOOKMAKERS:
            if name not in expected:
                return f"expected lacks {name}; a narrowed local run cannot serve as the release override"
    if record.get("passed") is not True:
        return "passed is not true; the recorded run did not pass"
    git_sha = record.get("git-sha")
    if not git_sha:
        return "git-sha is missing"
    if expected_sha and not _sha_matches(str(git_sha), expected_sha):
        return f"git-sha {git_sha} does not match the released commit {expected_sha}"
    return None


def main(argv: list[str]) -> int:
    if len(argv) not in (2, 3):
        print("usage: check_live_run.py <live-run.json | -> [expected-git-sha]", file=sys.stderr)
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
    expected_sha = argv[2] if len(argv) == 3 else None
    reason = check(record, datetime.now(timezone.utc), expected_sha)
    if reason:
        print(reason, file=sys.stderr)
        return 1
    counts = ", ".join(f"{name}={record['bookmakers'][name]}" for name in BOOKMAKERS)
    print(f"live-run.json accepted: ran-at {record['ran-at']}, {counts}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
