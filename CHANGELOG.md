# Changelog

## 0.4.0 — 2026-09-19

A call that cannot fetch odds now raises a typed exception instead of returning an empty list. An empty list means the bookmaker listed zero fixtures. Callers that treated `[]` as a failure must catch `NaijaBetError` or one of its subclasses: `BookmakerBlockedError` (an HTTP error or a bot wall, with `status` and `wall`), `BookmakerUnreachableError` (DNS or connection failure), `BookmakerTimeoutError`, and `ResponseParseError` (a JSON or shape failure). Each chains the transport error. One retry after 1 s follows a connection error or a 5xx answer; a 4xx answer never retries.

Removed: `sportybet_payload`, the `nairabetDNB` key, the `python -m NaijaBet_Api` entry point, `NaijaBet_Api.utils.logger`, and the empty `NaijaBet_Api.schema` package. `session_type` is accepted and ignored with a `DeprecationWarning`. `get_nations` and `get_competitions` raise `NotImplementedError`; `Betid.to_endpoint` accepts `bet9ja`, `betking`, and `nairabet` and raises `ValueError` for any other key.

Nairabet is rebuilt on its current API host. Its rows carry the same eleven keys as Bet9ja and Betking; `league`, `league_id`, and the three double-chance odds are new. The `time` field of every bookmaker is epoch seconds.

Sessions and timeouts: ten concurrent league fetches share one `aiohttp` session, the library closes only the sessions it created, and a caller-supplied session stays open. Every request carries a timeout (10 s connect, 30 s read by default) set by `timeout=` on the constructor. Constructing a bookmaker makes no network call. `get_all` returns the rows of every league that answered, stores each failed league's exception on `bookmaker.errors`, and raises only when every league failed.

`BetkingPlaywright` is synchronous only; its async methods raise `NotImplementedError`. A league request maps a Playwright timeout to `BookmakerTimeoutError` and a Playwright transport error to `BookmakerUnreachableError`; a failed browser start stops the browser before it raises.

Diagnostics go through `logging.getLogger("NaijaBet_Api.<module>")`; the package installs no handler. `Brotli` is a runtime dependency.

For maintainers: every release runs the live suite against the three bookmakers from a Lagos egress before it builds, and a maintainer can run the suite locally through the Lagos container (`make lagos`) or the proxy lane (`make live-proxy`); see `docs/runbooks/live-suite.md`.

## 0.3.1 — 2026-09-15

Nothing changes for a user of the library.

The release pipeline's smoke test against test.pypi.org now installs the package's dependencies from pypi.org only, and the package itself from test.pypi.org without dependencies. A release no longer stalls on an unrelated package that is hosted on test.pypi.org under a dependency's name.

## 0.3.0 — 2026-09-13

Python 3.10 or later is required. Installation on Python 3.8 or 3.9 now fails.

The pinned dependency set moved to current releases. This resolves 61 known security advisories across aiohttp, certifi, idna, requests, and urllib3.

- aiohttp: 3.7.4.post0 → 3.14.3
- requests: 2.26.0 → 2.34.2
- urllib3: 1.26.6 → 2.7.0
- certifi: 2021.5.30 → 2026.7.22
- idna: 3.2 → 3.19

The release workflow builds on Python 3.12.
