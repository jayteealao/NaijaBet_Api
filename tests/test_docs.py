"""Hold the shipped documents to the code: the exceptions reference, the README, and the computed version."""

import inspect
import re
import shutil
import subprocess
import time
from pathlib import Path

import pytest
from werkzeug.wrappers import Response

from NaijaBet_Api import exceptions
from NaijaBet_Api.bookmakers import Bet9ja
from NaijaBet_Api.id import Betid, endpoints

REPO = Path(__file__).resolve().parent.parent
README = REPO / "README.md"
REFERENCE = REPO / "docs" / "reference" / "exceptions.md"
EXAMPLE = re.compile(r"<!-- example:start -->\s*```python\n(.*?)```\s*<!-- example:end -->", re.S)
# The Akamai page as sports.bet9ja.com served it on 2026-09-17; the entities are the real encoding.
DENIED_BODY = (
    "<HTML><HEAD>\n"
    "<TITLE>Access Denied</TITLE>\n"
    "</HEAD><BODY>\n"
    "<H1>Access Denied</H1>\n"
    " \n"
    "You don't have permission to access "
    '"http&#58;&#47;&#47;sports&#46;bet9ja&#46;com&#47;desktop&#47;feapi&#47;PalimpsestAjax&#47;GetSports&#63;"'
    " on this server.<P>\n"
    "Reference&#32;&#35;18&#46;b8fd317&#46;1789664171&#46;1360c987\n"
    "<P>https&#58;&#47;&#47;errors&#46;edgesuite&#46;net&#47;18&#46;b8fd317&#46;1789664171&#46;1360c987</P>\n"
    "</BODY>\n"
    "</HTML>\n"
)
FAILURE_WORDS = ("fail", "error", "block", "down", "unavailable")


def exception_classes() -> set[str]:
    return {
        name
        for name, obj in inspect.getmembers(exceptions, inspect.isclass)
        if issubclass(obj, Exception) and obj.__module__ == exceptions.__name__
    }


def test_every_exception_class_has_a_heading():
    headings = set(re.findall(r"^## (\w+)$", REFERENCE.read_text(encoding="utf-8"), re.M))
    missing = exception_classes() - headings
    assert not missing, f"docs/reference/exceptions.md lacks a heading for {sorted(missing)}"


@pytest.fixture
def example_block() -> str:
    match = EXAMPLE.search(REFERENCE.read_text(encoding="utf-8"))
    assert match, "docs/reference/exceptions.md has no marked example block"
    return match.group(1)


@pytest.fixture
def stub_bet9ja(httpserver, monkeypatch):
    """Point the real Bet9ja class at the stub: the warm-up root and the league template."""
    monkeypatch.setitem(endpoints["bet9ja"], "leagues", httpserver.url_for("/league/{leagueid}"))
    monkeypatch.setattr(Bet9ja, "_url", httpserver.url_for("/"))
    httpserver.expect_request("/").respond_with_data("ok")
    return f"/league/{Betid.PREMIERLEAGUE.bet9ja_id}"


def test_reference_example_stops_on_a_block(example_block, stub_bet9ja, httpserver, capsys):
    httpserver.expect_request(stub_bet9ja).respond_with_data(DENIED_BODY, status=403)
    exec(compile(example_block, str(REFERENCE), "exec"), {})
    assert capsys.readouterr().out == "blocked: denied 403\n"


def test_reference_example_retries_one_timeout(example_block, stub_bet9ja, httpserver, capsys, bet9ja_payload):
    import json

    calls = []

    def handler(request):
        calls.append(request.path)
        if len(calls) == 1:
            time.sleep(1.5)  # longer than the example's read timeout of 1 s
        return Response(json.dumps(bet9ja_payload), status=200)

    httpserver.expect_request(stub_bet9ja).respond_with_handler(handler)
    exec(compile(example_block, str(REFERENCE), "exec"), {})
    out = capsys.readouterr().out.splitlines()
    assert out[0] == "timed out on attempt 1; retrying"
    assert re.fullmatch(r"\d+ rows", out[1]) and out[1] != "0 rows"
    assert len(calls) == 2


def test_readme_sample_time_is_epoch_seconds():
    times = re.findall(r'"time": (\d+),', README.read_text(encoding="utf-8"))
    assert times, "README has no JSON sample row with a time field"
    assert all(len(value) == 10 for value in times), times


def test_readme_names_the_contract():
    text = README.read_text(encoding="utf-8")
    required = [
        *sorted(exception_classes()),
        "bookmaker.errors",
        "aclose()",
        "close()",
        "timeout=",
        "sportybet_payload",
        "nairabetDNB",
        "session_type",
        "python -m NaijaBet_Api",
        "docs/reference/exceptions.md",
        "docs/runbooks/live-suite.md",
    ]
    missing = [name for name in required if name not in text]
    assert not missing, f"README does not mention {missing}"


def test_readme_has_no_empty_list_failure_claim():
    # A line that pairs "returns empty" with a failure word describes the pre-0.4.0 contract, unless it negates it.
    offending = [
        line
        for line in README.read_text(encoding="utf-8").splitlines()
        if re.search(r"return(s|ing)? (\[\]|(an )?empty)", line, re.I)
        and any(word in line.lower() for word in FAILURE_WORDS)
        and "never" not in line.lower()
    ]
    assert not offending, offending


@pytest.mark.skipif(shutil.which("git-cliff") is None, reason="git-cliff is not installed")
def test_bumped_version_is_0_4_0():
    out = subprocess.run(["git-cliff", "--bumped-version"], capture_output=True, text=True, cwd=REPO, check=True)
    assert out.stdout.strip() == "v0.4.0", out.stdout
