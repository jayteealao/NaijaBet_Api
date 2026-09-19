"""Record the bookmaker API hosts the library calls, as a browser sees them.

The script drives Chromium through each bookmaker's front door and then through the exact
Premier League URL the library builds, records a HAR limited to the bookmaker hosts, replaces
every cookie value and secret-bearing header or query value with ``REDACTED``, writes the
decoded Premier League bodies, and prints one table row per recorded request (with every query
parameter value masked). The maintainer copies the printed facts into
``tests/fixtures/endpoint-provenance.json``; the HAR itself is never committed.

Run it from a Nigerian egress (the bookmakers reject other regions):

    uv run python scripts/record_session.py --out .scratch/recordings/<stamp>
"""

from __future__ import annotations

import argparse
import base64
import json
import re
import socket
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from egress import egress

from NaijaBet_Api.bookmakers import Bet9ja, Betking, Nairabet
from NaijaBet_Api.id import Betid

HOST_FILTER = re.compile(r"https://[^/]*(bet9ja\.com|betking\.com|nairabet\.com|biahosted\.com)/")
SITES = {"bet9ja": Bet9ja, "betking": Betking, "nairabet": Nairabet}
COOKIE_HEADERS = {"cookie", "set-cookie"}
AUTH_HEADER_NAMES = {"authorization", "proxy-authorization"}
SECRET_NAME_RE = re.compile(r"token|secret|key|x-auth", re.IGNORECASE)
NAV_TIMEOUT_MS = 60_000


def is_secret_name(name: str) -> bool:
    """True when a header or query-parameter name is known to carry a secret value.

    Matches ``authorization``/``proxy-authorization`` exactly, and any other name containing
    ``token``, ``secret``, ``key`` (which also covers ``api-key``/``apikey``), or ``x-auth``.
    """
    lowered = name.lower()
    return lowered in AUTH_HEADER_NAMES or SECRET_NAME_RE.search(lowered) is not None


def headers_of(cls) -> tuple[str | None, dict[str, str]]:
    """Split a bookmaker class's headers into (user-agent, the rest); the sites deny HeadlessChrome."""
    user_agent = None
    rest = {}
    for name, value in cls._headers.items():
        if name.lower() == "user-agent":
            user_agent = value
        else:
            rest[name] = value
    return user_agent, rest


def record(out: Path, headed: bool) -> Path:
    """Visit each site root and each library URL with the library's own headers.

    Playwright writes one HAR per context when the context closes, so each bookmaker gets its
    own context and file; the files are merged into ``session.har`` afterwards.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:  # pragma: no cover - depends on the local install
        sys.exit(
            'playwright is not installed: run pip install "NaijaBet_Api[playwright]" && playwright install chromium'
        )

    parts = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=not headed)
        for name, cls in SITES.items():
            part = out / f"{name}.har"
            user_agent, extra = headers_of(cls)
            context = browser.new_context(
                record_har_path=str(part),
                record_har_url_filter=HOST_FILTER,
                record_har_content="embed",
                user_agent=user_agent,
                extra_http_headers=extra,
            )
            page = context.new_page()
            page.set_default_navigation_timeout(NAV_TIMEOUT_MS)
            for url in (cls._url, Betid.PREMIERLEAGUE.to_endpoint(name)):
                try:
                    page.goto(url, wait_until="domcontentloaded")
                except Exception as exc:  # noqa: BLE001 - a failed visit is data for the table
                    print(f"visit failed: {url} -> {type(exc).__name__}: {str(exc).splitlines()[0]}")
            context.close()
            parts.append(part)
        browser.close()

    merged = json.loads(parts[0].read_text(encoding="utf-8"))
    for part in parts[1:]:
        merged["log"]["entries"].extend(json.loads(part.read_text(encoding="utf-8"))["log"]["entries"])
    har = out / "session.har"
    har.write_text(json.dumps(merged, indent=1), encoding="utf-8")
    for part in parts:
        part.unlink()
    return har


def redact_query(request: dict) -> int:
    """Replace secret-looking query parameter values in a request's URL and ``queryString``.

    A parameter is redacted when its name matches ``is_secret_name`` (for example a ``key`` or
    ``token`` parameter); other parameters, like ``league``, are left as recorded.
    """
    url = request.get("url", "")
    parts = urlsplit(url)
    if not parts.query:
        return 0
    count = 0
    redacted_pairs = []
    for name, value in parse_qsl(parts.query, keep_blank_values=True):
        if is_secret_name(name) and value != "REDACTED":
            value = "REDACTED"
            count += 1
        redacted_pairs.append((name, value))
    if count:
        request["url"] = urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(redacted_pairs), parts.fragment))
        if "queryString" in request:
            request["queryString"] = [{"name": name, "value": value} for name, value in redacted_pairs]
    return count


def redact(har: Path) -> int:
    """Replace every cookie value and secret-bearing header or query value with REDACTED.

    Headers are redacted when the (lower-cased) name is a cookie header or matches
    ``is_secret_name`` (``authorization``, ``proxy-authorization``, or a name containing
    ``token``, ``secret``, ``key``, or ``x-auth``). Query parameters in a request's URL are
    redacted the same way; other query parameters are left untouched. Returns the count of
    values replaced.
    """
    data = json.loads(har.read_text(encoding="utf-8"))
    count = 0
    for entry in data["log"]["entries"]:
        for side in ("request", "response"):
            for header in entry[side].get("headers", []):
                name = header["name"].lower()
                if name in COOKIE_HEADERS or is_secret_name(name):
                    header["value"] = "REDACTED"
                    count += 1
            for cookie in entry[side].get("cookies", []):
                cookie["value"] = "REDACTED"
                count += 1
        count += redact_query(entry["request"])
    har.write_text(json.dumps(data, indent=1), encoding="utf-8")
    return count


def entries(har: Path) -> list[dict]:
    return json.loads(har.read_text(encoding="utf-8"))["log"]["entries"]


def body_of(entry: dict) -> bytes:
    content = entry["response"].get("content", {})
    text = content.get("text", "")
    if content.get("encoding") == "base64":
        return base64.b64decode(text)
    return text.encode("utf-8")


def write_bodies(har: Path, out: Path) -> dict[str, int]:
    """Write the decoded Premier League body per bookmaker; return the status per bookmaker."""
    statuses: dict[str, int] = {}
    by_url = {entry["request"]["url"]: entry for entry in entries(har)}
    for name in SITES:
        url = Betid.PREMIERLEAGUE.to_endpoint(name)
        entry = by_url.get(url)
        if entry is None:
            statuses[name] = 0
            continue
        statuses[name] = entry["response"]["status"]
        (out / f"{name}-premier-league.json").write_bytes(body_of(entry))
    return statuses


def masked_path(url: str) -> str:
    """Return ``url``'s path and query with every query parameter value replaced by ``***``.

    Parameter names are kept so the printed table stays readable; this masks every value,
    not only secret-looking ones, since the table is meant to be pasted into a pull request.
    """
    parts = urlsplit(url)
    if not parts.query:
        return parts.path
    masked = "&".join(f"{name}=***" for name, _ in parse_qsl(parts.query, keep_blank_values=True))
    return f"{parts.path}?{masked}"


def print_table(har: Path) -> None:
    print(f"{'host':45} {'path':70} {'status':>6} content-type")
    for entry in entries(har):
        parts = urlsplit(entry["request"]["url"])
        path = masked_path(entry["request"]["url"])
        content_type = entry["response"].get("content", {}).get("mimeType", "")
        print(f"{parts.hostname:45} {path[:70]:70} {entry['response']['status']:>6} {content_type}")


def resolve(har: Path) -> dict[str, str]:
    hosts = sorted({urlsplit(entry["request"]["url"]).hostname for entry in entries(har)})
    resolved = {}
    for host in hosts:
        try:
            resolved[host] = socket.gethostbyname(host)
        except OSError as exc:
            resolved[host] = f"unresolved: {exc}"
    return resolved


def main(argv: list[str] | None = None) -> int:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", type=Path, default=Path(".scratch/recordings") / stamp, help="output directory")
    parser.add_argument("--headed", action="store_true", help="show the browser window")
    parser.add_argument(
        "--no-egress-check", action="store_true", help="skip the ipinfo check that the egress country is NG"
    )
    args = parser.parse_args(argv)

    where = egress()
    if not args.no_egress_check and where.get("country") != "NG":
        sys.exit(
            f"egress is {where.get('country')} ({where.get('ip')}), not NG; connect the VPN or pass --no-egress-check"
        )

    args.out.mkdir(parents=True, exist_ok=True)
    har = record(args.out, args.headed)
    redacted = redact(har)
    statuses = write_bodies(har, args.out)
    print_table(har)
    print()
    print(
        json.dumps(
            {
                "recorded-at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "egress": where,
                "resolved": resolve(har),
                "premier-league-status": statuses,
                "cookie-values-redacted": redacted,
                "har": str(har),
            },
            indent=1,
        )
    )
    return 0 if all(status == 200 for status in statuses.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
