"""``redact()`` and ``masked_path()`` scrub secrets from a recorded HAR and its printed table."""

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))

from record_session import masked_path, redact  # noqa: E402


def _har(tmp_path: Path) -> Path:
    data = {
        "log": {
            "entries": [
                {
                    "request": {
                        "url": "https://api.bet9ja.com/sports?key=abc123&league=1",
                        "headers": [
                            {"name": "authorization", "value": "Bearer secret-token"},
                            {"name": "x-api-token", "value": "another-secret"},
                            {"name": "cookie", "value": "session=abc"},
                            {"name": "accept", "value": "application/json"},
                        ],
                        "cookies": [{"name": "session", "value": "abc"}],
                        "queryString": [
                            {"name": "key", "value": "abc123"},
                            {"name": "league", "value": "1"},
                        ],
                    },
                    "response": {
                        "status": 200,
                        "headers": [{"name": "set-cookie", "value": "session=abc; Path=/"}],
                        "content": {"mimeType": "application/json"},
                    },
                }
            ]
        }
    }
    har = tmp_path / "session.har"
    har.write_text(json.dumps(data), encoding="utf-8")
    return har


def test_redact_scrubs_auth_headers_cookies_and_token_query_values(tmp_path):
    har = _har(tmp_path)

    count = redact(har)

    data = json.loads(har.read_text(encoding="utf-8"))
    request = data["log"]["entries"][0]["request"]
    response = data["log"]["entries"][0]["response"]
    request_headers = {h["name"]: h["value"] for h in request["headers"]}
    response_headers = {h["name"]: h["value"] for h in response["headers"]}

    assert request_headers["authorization"] == "REDACTED"
    assert request_headers["x-api-token"] == "REDACTED"
    assert request_headers["cookie"] == "REDACTED"
    assert request_headers["accept"] == "application/json"
    assert response_headers["set-cookie"] == "REDACTED"
    assert request["cookies"][0]["value"] == "REDACTED"

    query = {q["name"]: q["value"] for q in request["queryString"]}
    assert query["key"] == "REDACTED"
    assert query["league"] == "1"
    assert "abc123" not in request["url"]
    assert "league=1" in request["url"]
    assert count > 0


def test_masked_path_hides_every_query_value_but_keeps_names():
    path = masked_path("https://api.bet9ja.com/sports?key=abc123&league=1")

    assert path == "/sports?key=***&league=***"


def test_masked_path_without_a_query_returns_the_bare_path():
    assert masked_path("https://api.bet9ja.com/sports") == "/sports"
