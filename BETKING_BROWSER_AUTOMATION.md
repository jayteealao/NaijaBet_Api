# Betking through a browser: `BetkingPlaywright`

## When you need this

`Betking` fetches over plain HTTP requests, the same as `Bet9ja` and `Nairabet`, and works from a Nigerian egress: the live suite fetched 144 Betking rows on 2026-09-16 from a Lagos egress with the plain class. From another egress the Betking API answers 403 and the library raises `BookmakerBlockedError` with wall `denied` (or `challenge` when a Cloudflare page answers).

`BetkingPlaywright` is the fallback for that case. It extends `Betking` and fetches each league URL through a Chromium page after loading `https://betking.com/sports`, so the request carries the cookies and headers a real browser session carries. When the egress is Nigerian, use plain `Betking`. When the egress is not Nigerian, or when plain `Betking` raises `BookmakerBlockedError` from Nigeria, use `BetkingPlaywright`.

## Install

```
pip install "NaijaBet_Api[playwright]"
playwright install chromium
```

The `playwright` extra installs the `playwright` package without a version pin. When the `playwright` package is absent, `from NaijaBet_Api.bookmakers import BetkingPlaywright` raises `ImportError`.

## Use BetkingPlaywright

```python
from NaijaBet_Api.bookmakers import BetkingPlaywright
from NaijaBet_Api.id import Betid

with BetkingPlaywright() as betking:
    rows = betking.get_league(Betid.PREMIERLEAGUE)
    all_rows = betking.get_all()
    arsenal = betking.get_team("Arsenal")
```

- `BetkingPlaywright(headless=True, timeout=30000)`: `headless=False` shows the browser window; `timeout`, in milliseconds, applies to the first visit to `betking.com/sports` and to every league request.
- The context manager starts the browser on entry and stops it on exit. Without the context manager, the first `get_league` call starts the browser; call `_stop_browser()` to release it.
- One browser serves every call on the instance; `get_all` fetches the ten leagues through the same page.
- The rows have the same eleven keys as the other bookmakers; `time` is epoch seconds.

A non-200 answer raises `BookmakerBlockedError`, and a bad body raises `ResponseParseError`, the same classes as the other bookmakers. A browser transport failure or a Playwright timeout raises Playwright's own error; that error is not a `NaijaBetError`, so `get_all` does not record it in `errors` and stops at that league. A non-200 answer on the browser's first visit to `betking.com/sports` is only logged as a warning. `get_all` records `NaijaBetError` failures per league in `betking.errors` and raises `NaijaBetError` only when every league failed. See [docs/reference/exceptions.md](docs/reference/exceptions.md).

```python
from NaijaBet_Api import BookmakerBlockedError

with BetkingPlaywright() as betking:
    try:
        rows = betking.get_league(Betid.LALIGA)
    except BookmakerBlockedError as exc:
        print(f"blocked: {exc.wall} {exc.status}")
```

## Limits

- Synchronous only. `async_get_league`, `async_get_all`, and `async_session` raise `NotImplementedError`; use `get_league` and `get_all`.
- One Chromium process per instance; a fetch takes seconds where the plain class takes milliseconds. Reuse one instance for a batch of leagues.
- A Chromium build must be installed on the machine (`playwright install chromium`); on a CI runner use `playwright install --with-deps chromium`.
- The browser session is not a guarantee: a bookmaker can deny a browser from a non-Nigerian egress as well. When that happens the class raises `BookmakerBlockedError`; a Nigerian egress is the remaining option.
- The inherited `close()` releases the HTTP session only; the browser stops through the context manager or `_stop_browser()`.

## Example

[examples/betking_playwright_example.py](examples/betking_playwright_example.py) runs seven scenarios: the context manager, several leagues, team search, a comparison with Bet9ja and Nairabet, manual browser management, all leagues, and error handling with the typed exceptions.

```
uv run python examples/betking_playwright_example.py
```
