# NaijaBet-Api

[![ci](https://github.com/jayteealao/NaijaBet_Api/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/jayteealao/NaijaBet_Api/actions/workflows/ci.yml) [![release](https://github.com/jayteealao/NaijaBet_Api/actions/workflows/release.yml/badge.svg)](https://github.com/jayteealao/NaijaBet_Api/actions/workflows/release.yml) [![PyPI](https://img.shields.io/pypi/v/NaijaBet-Api)](https://pypi.org/project/NaijaBet-Api/)

A python library that provides access to the odds data of Nigeria's major betting sites.

It provides access to Bet9ja, Betking and Nairabet's 1X2 and doublechance soccer odds.

## Requirements

Python 3.10 or later. Python 3.8 and 3.9 are not supported since version 0.3.0.

```
pip install NaijaBet_Api
```

The `brotli` package is installed as a dependency; the Nairabet API compresses its answers with Brotli.

The bookmakers answer requests from a Nigerian egress. From any other egress Bet9ja and Betking answer 403, and the library raises `BookmakerBlockedError` (see [Failure contract](#failure-contract)). Connect through a Nigerian egress, or use `BetkingPlaywright` for Betking (see [Betking from outside Nigeria](#betking-from-outside-nigeria)).

## Quick start

All three bookmakers work over plain HTTP requests:

```python
from NaijaBet_Api.bookmakers import Bet9ja, Betking, Nairabet
from NaijaBet_Api.id import Betid

bet9ja = Bet9ja()
betking = Betking()
nairabet = Nairabet()

# One league
rows = bet9ja.get_league(Betid.PREMIERLEAGUE)

# All ten leagues on one session; failed leagues land in bet9ja.errors
all_rows = bet9ja.get_all()

# Rows whose match name contains a team
arsenal = nairabet.get_team("Arsenal")
```

`get_league`, `get_all`, and `get_team` return a list of dicts with eleven keys. `time` is the kick-off in epoch seconds. Row captured on 2026-09-16 from a Lagos egress:

```json
{
  "match": "Brentford - Chelsea",
  "league": "Premier League",
  "time": 1789758000,
  "league_id": 170880,
  "match_id": 831880021,
  "home": 2.86,
  "draw": 3.8,
  "away": 2.32,
  "home_or_draw": 1.62,
  "home_or_away": 1.27,
  "draw_or_away": 1.43
}
```

An empty list means the bookmaker listed no fixtures for that league. A failure never returns an empty list; it raises.

The endpoints come from a recording made in a browser (`tests/fixtures/endpoint-provenance.json`). Bet9ja answers from `sports.bet9ja.com`, Betking from `sportsapicdn-desktop.betking.com`, and Nairabet from its Altenar widget API at `sb2frontend-altenar2.biahosted.com`; the former `sports-api.nairabet.com` host no longer resolves.

## Failure contract

Every fetch raises a subclass of `NaijaBetError`:

| Class | Raised when |
|---|---|
| `BookmakerBlockedError` | The bookmaker answered a status other than 200. `status` holds the code; `wall` is `challenge` (Cloudflare), `denied` (Akamai, the usual answer to a non-Nigerian egress), or `http`. |
| `BookmakerUnreachableError` | No HTTP response arrived: DNS, connection, or transport failure. |
| `BookmakerTimeoutError` | The connect or read timeout elapsed. Also a `TimeoutError`. |
| `ResponseParseError` | The bookmaker answered 200 with a body the normalizer does not recognise. |

`get_all` and `async_get_all` fetch the ten leagues, record each failed league in `bookmaker.errors` (a `dict[Betid, NaijaBetError]`), and raise `NaijaBetError` only when every league failed. The library retries once, after one second, for a refused or dropped connection and for a 5xx status; a timeout, a 4xx status, and a parse failure are not retried. `BetkingPlaywright` does not retry: its single browser request raises on the first non-200 answer.

```python
from NaijaBet_Api import BookmakerBlockedError, BookmakerTimeoutError

try:
    rows = bet9ja.get_league(Betid.LALIGA)
except BookmakerBlockedError as exc:
    print(f"blocked: {exc.wall} {exc.status}")
except BookmakerTimeoutError:
    print("timed out")
```

Each class, its fields, the wall values, and the retry rule are in [docs/reference/exceptions.md](docs/reference/exceptions.md).

## Sessions

The constructor makes no network call. `timeout=(connect, read)` in seconds applies to every request on both transports; the default is `(10, 30)`. The blocking session is created on the first fetch and reused across leagues; `close()` releases it. The async methods share one `aiohttp` session across the ten leagues; `aclose()` releases it. A caller-supplied `async_session` is used as given and never closed. `BetkingPlaywright` is the exception: its `timeout`, one integer of milliseconds, applies to the first page visit and to every league request; the browser is released by the context manager or `_stop_browser()`, not by `close()`.

```python
import asyncio
from NaijaBet_Api.bookmakers import Nairabet


async def main():
    nairabet = Nairabet(timeout=(5, 20))
    try:
        rows = await nairabet.async_get_all()
    finally:
        await nairabet.aclose()


asyncio.run(main())
```

## Betking from outside Nigeria

`Betking` works over plain requests from a Nigerian egress. From another egress the site answers 403 and the library raises `BookmakerBlockedError` with wall `denied`. `BetkingPlaywright` drives a Chromium page instead and needs the `playwright` extra:

```
pip install "NaijaBet_Api[playwright]"
playwright install chromium
```

```python
from NaijaBet_Api.bookmakers import BetkingPlaywright
from NaijaBet_Api.id import Betid

with BetkingPlaywright() as betking:
    rows = betking.get_league(Betid.PREMIERLEAGUE)
```

`BetkingPlaywright` is synchronous only: `async_get_league`, `async_get_all`, and `async_session` raise `NotImplementedError`. A non-200 answer raises `BookmakerBlockedError` and a bad body raises `ResponseParseError`, as for the other bookmakers; a browser transport failure or a Playwright timeout raises Playwright's own error, which `get_all` does not record in `errors`. See [BETKING_BROWSER_AUTOMATION.md](BETKING_BROWSER_AUTOMATION.md) and [examples/betking_playwright_example.py](examples/betking_playwright_example.py).

## Live gate

Every release runs the live suite against the three bookmakers from a Lagos egress before it builds; a bookmaker that returns zero rows or a `BookmakerBlockedError` blocks the release. The latest recorded run and the endpoint hosts are in [TESTING_PROOF.md](TESTING_PROOF.md); the maintainer procedure is in [docs/runbooks/live-suite.md](docs/runbooks/live-suite.md).

## Changes since 0.3

Version 0.4.0, the release after 0.3.1, removes `sportybet_payload`, the `nairabetDNB` key, and the `python -m NaijaBet_Api` entry point; `session_type` is still accepted by the constructor and ignored (a `DeprecationWarning` is emitted). A failed fetch raises a typed exception; the empty-list signal of 0.3 is gone. The changelog carries the detail per version.

## TODO

- [ ] Add Sportybet
- [ ] Add all soccer leagues
- [ ] Add access to available bookmaker odds for specific matches (`get_nations`, `get_competitions` raise `NotImplementedError`)
