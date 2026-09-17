# Exceptions

Every fetch method of a bookmaker (`get_league`, `get_all`, `get_team`, `async_get_league`, `async_get_all`) returns a list of rows or raises one of the classes below. An empty list means the bookmaker answered with zero fixtures for that league; it never means a failure. All classes live in `NaijaBet_Api.exceptions` and are re-exported from the `NaijaBet_Api` package.

`get_all` and `async_get_all` fetch the ten leagues and record each failed league in `bookmaker.errors`, a `dict[Betid, NaijaBetError]`. They raise only when every league failed. After a call, read `bookmaker.errors` to see which leagues failed and why.

## NaijaBetError

Base: `Exception`.

Fields: `bookmaker` (the bookmaker name: `bet9ja`, `betking`, `nairabet`), `message`.

Raised directly by `get_all` and `async_get_all` when all ten leagues failed; the message reads `all 10 leagues failed; see .errors`, and `bookmaker.errors` holds the cause per league. Catch this class to handle every library failure in one place.

## BookmakerBlockedError

Base: `NaijaBetError`.

Fields: `bookmaker`, `status` (the HTTP status code), `wall` (see the table below), `body_excerpt` (the first 200 characters of the response body).

Raised when the bookmaker answered with a status other than 200. A 5xx status with wall `http` is retried once after 1.0 s; a second non-200 answer raises. A 403 or 404 raises at once. `BetkingPlaywright` raises on the first non-200 answer from the browser request; it does not retry.

## BookmakerUnreachableError

Base: `NaijaBetError`.

Fields: `bookmaker`, `message` (the transport error text).

Raised when no HTTP response arrived: DNS failure, refused connection, or a transport error. A connection error is retried once after 1.0 s before this class is raised.

## BookmakerTimeoutError

Base: `BookmakerUnreachableError`, `TimeoutError`.

Fields: `bookmaker`, `message` (`timed out after (connect, read) s`, with the configured pair).

Raised when the connect timeout or the read timeout elapsed before a response arrived. The timeout comes from the constructor: `Bet9ja(timeout=(10, 30))` is the default, in seconds. A timeout is not retried. Because the class also subclasses the built-in `TimeoutError`, an `except TimeoutError:` clause catches it.

## ResponseParseError

Base: `NaijaBetError`.

Fields: `bookmaker`, `message`.

Raised when the bookmaker answered 200 but the body is not the JSON shape the normalizer expects, and on the async transport when the response body cannot be decoded. The messages are `response is not JSON`, `response shape not recognised`, `validator path missing from response`, and `response body could not be decoded: <cause>`. A parse failure is not retried.

## Wall values

`classify_wall(status, body)` names the wall behind a non-200 answer. The value lands in `BookmakerBlockedError.wall`.

| `wall` | Meaning | Detection |
|---|---|---|
| `challenge` | A Cloudflare challenge page answered instead of the API. | The body contains `Just a moment` or `cf-mitigated`. |
| `denied` | An Akamai access-denied page answered instead of the API. The usual cause is an egress outside Nigeria. | The body, after HTML entities are decoded, contains `Access Denied` and `Reference #`. |
| `http` | Any other non-200 status. | Neither pattern matched. |

## Retry rule

The library retries at most once, after a delay of 1.0 s, and only for two conditions:

- a transport error on the blocking or the async transport (`requests.ConnectionError`, `aiohttp.ClientConnectionError`);
- a 5xx status whose wall is `http`.

A timeout, a 4xx status, a `challenge` or `denied` wall, and a parse failure are not retried. A caller that wants more attempts wraps the call, as the example below does for a timeout. `BetkingPlaywright` does not retry: its single browser request raises on the first non-200 answer.

## Caller example

The example retries one timeout and stops on a block. It closes the blocking session in `finally`; `aclose()` is the async form.

<!-- example:start -->
```python
from NaijaBet_Api.bookmakers import Bet9ja
from NaijaBet_Api.exceptions import BookmakerBlockedError, BookmakerTimeoutError
from NaijaBet_Api.id import Betid

bookmaker = Bet9ja(timeout=(1, 1))
try:
    for attempt in (1, 2):
        try:
            rows = bookmaker.get_league(Betid.PREMIERLEAGUE)
        except BookmakerTimeoutError:
            print(f"timed out on attempt {attempt}; retrying")
            continue
        except BookmakerBlockedError as exc:
            print(f"blocked: {exc.wall} {exc.status}")
            break
        print(f"{len(rows)} rows")
        break
finally:
    bookmaker.close()
```
<!-- example:end -->

From an egress outside Nigeria, Bet9ja answers 403 and the example prints `blocked: denied 403`. From Lagos, the example prints the row count.
