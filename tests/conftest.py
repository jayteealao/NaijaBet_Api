"""
Pytest configuration for NaijaBet API tests.

The offline suite drives the library against a local ``pytest-httpserver`` stub
and a raw-socket "blackhole" that accepts a connection and never answers.
"""

import json
import socket
import subprocess
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path

import brotli
import pytest
from werkzeug.wrappers import Response

import NaijaBet_Api.bookmakers.BaseClass as base_module
from NaijaBet_Api.bookmakers.BaseClass import BookmakerBaseClass
from NaijaBet_Api.bookmakers.nairabet import Nairabet
from NaijaBet_Api.id import Betid, endpoints
from NaijaBet_Api.utils import jsonpaths
from NaijaBet_Api.utils.normalizer import bet9ja_match_normalizer

FIXTURES = Path(__file__).parent / "fixtures"
REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))

from egress import egress  # noqa: E402 - shared with scripts/record_session.py

# Per-bookmaker row counts stashed by the live suite; ``--live-record`` writes them out.
COUNTS = pytest.StashKey[dict]()


# Configure pytest-asyncio
def pytest_configure(config):
    config.addinivalue_line("markers", "asyncio: mark test as an asyncio test")


def pytest_addoption(parser):
    parser.addoption("--live-record", default=None, metavar="PATH", help="write the live-run record to PATH")


def pytest_sessionfinish(session, exitstatus):
    """Write the dated record the release override reads: ``make live`` passes ``--live-record``."""
    path = session.config.getoption("--live-record")
    if path is None:
        return
    record = {
        "ran-at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "egress": egress(),
        "bookmakers": dict(session.config.stash.get(COUNTS, {})),
        "git-sha": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip(),
        "passed": int(exitstatus) == 0,
    }
    Path(path).write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")


@pytest.fixture(scope="session")
def httpserver_listen_address():
    """Bind the stub to 127.0.0.1; ``localhost`` resolves to ``::1`` first on Windows and costs ~2 s per request."""
    return ("127.0.0.1", 0)


@pytest.fixture(scope="session")
def bet9ja_payload() -> dict:
    """The canned Bet9ja league payload, three events."""
    return json.loads((FIXTURES / "bet9ja_league.json").read_text(encoding="utf-8"))


@pytest.fixture
def stub(httpserver, monkeypatch):
    """A concrete bookmaker class whose root and league URLs point at the stub server."""
    monkeypatch.setitem(endpoints["bet9ja"], "leagues", httpserver.url_for("/league/{leagueid}"))
    httpserver.expect_request("/").respond_with_data("ok")

    class StubBookmaker(BookmakerBaseClass):
        _site = "bet9ja"
        _url = httpserver.url_for("/")
        _headers = {"user-agent": "naijabet-tests"}

        def normalizer(self, data):
            return bet9ja_match_normalizer(jsonpaths.bet9ja_validator(data))

    return StubBookmaker


@pytest.fixture
def league_routes(httpserver, bet9ja_payload):
    """Register league routes on the stub.

    ``serve(status=200, body=None, headers=None, leagues=Betid, sequence=None)``:
    Without ``body`` each league serves the canned payload with its own league id and match ids,
    so rows from different leagues never collapse in the dedupe. ``sequence`` is a list of
    ``(status, body)`` pairs answered in order for each league;
    the last pair repeats once the list is exhausted. A per-path counter replaces
    ``expect_ordered_request``, which puts the server into permanent failure when any
    other route is hit while an ordered handler is pending.
    """

    def per_league_body(league):
        payload = json.loads(json.dumps(bet9ja_payload))
        for event in payload["D"]["E"]:
            event["GID"] = league.bet9ja_id
            event["ID"] = event["ID"] * 1000 + league.bet9ja_id
        return json.dumps(payload)

    def serve(status=200, body=None, headers=None, leagues=Betid, sequence=None):
        for league in leagues:
            league_body = per_league_body(league) if body is None else body
            path = f"/league/{league.bet9ja_id}"
            if sequence:
                steps = list(sequence)

                def handler(request, steps=steps):
                    step_status, step_body = steps.pop(0) if len(steps) > 1 else steps[0]
                    return Response(step_body, status=step_status)

                httpserver.expect_request(path).respond_with_handler(handler)
            else:
                httpserver.expect_request(path).respond_with_data(league_body, status=status, headers=headers)

    return serve


@pytest.fixture
def league_log(httpserver):
    """Return the stub requests whose path starts with ``/league/``; the warm-up GET hits ``/`` only."""

    def read():
        return [req for req, _ in httpserver.log if req.path.startswith("/league/")]

    return read


@pytest.fixture
def blackhole():
    """A TCP listener that accepts connections and never sends a byte."""
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.bind(("127.0.0.1", 0))
    listener.listen(5)
    port = listener.getsockname()[1]
    accepted: list[socket.socket] = []
    stop = threading.Event()

    def accept_loop():
        listener.settimeout(0.2)
        while not stop.is_set():
            try:
                conn, _ = listener.accept()
            except (socket.timeout, OSError):
                continue
            accepted.append(conn)

    thread = threading.Thread(target=accept_loop, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{port}"
    stop.set()
    thread.join(timeout=2)
    for conn in accepted:
        conn.close()
    listener.close()


@pytest.fixture
def closed_port():
    """A local URL on a port that nothing listens on."""
    probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    probe.bind(("127.0.0.1", 0))
    port = probe.getsockname()[1]
    probe.close()
    return f"http://127.0.0.1:{port}"


@pytest.fixture
def no_retry_sleep(monkeypatch):
    """Replace the retry sleeps in the base module with recorders; return the two call lists."""
    sync_calls: list[float] = []
    async_calls: list[float] = []

    def fake_sleep(seconds):
        sync_calls.append(seconds)

    async def fake_async_sleep(seconds):
        async_calls.append(seconds)

    monkeypatch.setattr(base_module.time, "sleep", fake_sleep)
    monkeypatch.setattr(base_module.asyncio, "sleep", fake_async_sleep)
    return sync_calls, async_calls


@pytest.fixture
def brotli_body(bet9ja_payload) -> bytes:
    """The canned payload compressed with brotli, for a ``Content-Encoding: br`` route."""
    return brotli.compress(json.dumps(bet9ja_payload).encode())


@pytest.fixture
def point_at(monkeypatch):
    """Point a bookmaker class's league template at an arbitrary base URL."""

    def apply(base_url: str):
        monkeypatch.setitem(endpoints["bet9ja"], "leagues", base_url + "/league/{leagueid}")

    return apply


@pytest.fixture
def nairabet_payload() -> dict:
    """A canned Altenar ``GetEvents`` body: three Premier League events with their 1x2 and double-chance markets."""
    return json.loads((FIXTURES / "nairabet_league.json").read_text(encoding="utf-8"))


@pytest.fixture
def nairabet_stub(httpserver, monkeypatch, nairabet_payload):
    """The real ``Nairabet`` class with its warm-up and league URLs pointed at the stub server."""
    monkeypatch.setitem(endpoints["nairabet"], "leagues", httpserver.url_for("/GetEvents?champIds={leagueid}"))
    monkeypatch.setattr(Nairabet, "_url", httpserver.url_for("/GetTopSportMenu"))
    httpserver.expect_request("/GetTopSportMenu").respond_with_json({})
    httpserver.expect_request("/GetEvents").respond_with_json(nairabet_payload)
    return Nairabet
