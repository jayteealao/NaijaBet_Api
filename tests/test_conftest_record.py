"""A mistyped ``LIVE_EXPECT`` must not abort ``pytest_sessionfinish`` before it writes a record."""

import json
from pathlib import Path

import pytest

from tests import conftest


class _StubConfig:
    """The slice of ``pytest.Config`` the hook touches: ``getoption`` and ``stash``."""

    def __init__(self, record_path: Path):
        self._record_path = record_path
        self.stash = pytest.Stash()

    def getoption(self, name):
        assert name == "--live-record"
        return str(self._record_path)


class _StubSession:
    def __init__(self, record_path: Path):
        self.config = _StubConfig(record_path)


def test_mistyped_live_expect_still_writes_a_record(tmp_path, monkeypatch):
    monkeypatch.setenv("LIVE_EXPECT", "not-a-real-bookmaker")
    monkeypatch.setattr(conftest, "egress", lambda: {"ip": None, "city": None, "country": None, "org": None})
    record_path = tmp_path / "live-run.json"

    conftest.pytest_sessionfinish(_StubSession(record_path), 0)

    record = json.loads(record_path.read_text(encoding="utf-8"))
    assert record["expected"] == []
    assert "not-a-real-bookmaker" in record["expected-error"]
    assert record["bookmakers"] == {}
    assert record["passed"] is True


def test_egress_failure_still_writes_a_record(tmp_path, monkeypatch):
    def boom():
        raise RuntimeError("ipinfo unreachable")

    monkeypatch.setattr(conftest, "egress", boom)
    record_path = tmp_path / "live-run.json"

    conftest.pytest_sessionfinish(_StubSession(record_path), 0)

    record = json.loads(record_path.read_text(encoding="utf-8"))
    assert record["egress"] is None
    assert record["egress-error"] == "ipinfo unreachable"
