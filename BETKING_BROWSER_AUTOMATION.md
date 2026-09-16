# Betking through a browser: `BetkingPlaywright`

## When you need this

`Betking` fetches over plain HTTP requests, the same as `Bet9ja` and `Nairabet`, and works from a Nigerian egress: the live suite fetched 144 Betking rows on 2026-09-16 from a Lagos exit with the plain class. From another egress the Betking API answers 403 and the library raises `BookmakerBlockedError` with wall `denied` (or `challenge` when a Cloudflare page answers).

`BetkingPlaywright` is the fallback for that case. It extends `Betking` and fetches each league URL through a Chromium page after loading `https://betking.com/sports`, so the request carries the cookies and headers a real browser session carries. Prefer plain `Betking` when the egress is Nigerian; use `BetkingPlaywright` when it is not, or when the plain class raises `BookmakerBlockedError` from Nigeria.

## Install

```
pip install "NaijaBet_Api[playwright]"
playwright install chromium
```

The `playwright` extra pins `playwright>=1.62.0`. `BetkingPlaywright` imports only when the package is installed; `from NaijaBet_Api.bookmakers import BetkingPlaywright` raises `ImportError` otherwise.

## Use BetkingPlaywright

```python
from NaijaBet_Api.bookmakers import BetkingPlaywright
from NaijaBet_Api.id import Betid

with BetkingPlaywright() as betking:
    rows = betking.get_league(Betid.PREMIERLEAGUE)
    all_rows = betking.get_all()
    arsenal = betking.get_team("Arsenal")
```

- `BetkingPlaywright(headless=True, timeout=30000)`: `headless=False` shows the browser window; `timeout` is the page's default timeout for navigation and requests, in milliseconds.
- The context manager starts the browser on entry and stops it on exit. Without the context manager, the first `get_league` call starts the browser; call `_stop_browser()` to release it.
- One browser serves every call on the instance; `get_all` fetches the ten leagues through the same page.
- The rows have the same eleven keys as the other bookmakers; `time` is epoch seconds.

Failures raise the same exceptions as the other bookmakers: `BookmakerBlockedError` when the page request answers a status other than 200 (a non-200 answer on the browser's first visit to `betking.com/sports` is only logged as a warning), and `ResponseParseError` when the body is not the expected JSON. `get_all` records per-league failures in `betking.errors` and raises `NaijaBetError` only when every league failed. See [docs/reference/exceptions.md](docs/reference/exceptions.md).

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

## Example

[examples/betking_playwright_example.py](examples/betking_playwright_example.py) runs seven scenarios: the context manager, several leagues, team search, a comparison with Bet9ja and Nairabet, manual browser management, all leagues, and error handling with the typed exceptions.

```
uv run python examples/betking_playwright_example.py
```
