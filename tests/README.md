# Tests

The suite has two halves. The offline half runs on every push and every pull request against a local `pytest-httpserver` stub; it needs no network. The live half calls the three bookmakers from a Nigerian egress and runs through `make live` and the `live` workflow.

## Layout

| File | Covers | Half |
|---|---|---|
| `test_contract.py` | `BookmakerBaseClass`: lazy sessions, the `timeout=` pair, the typed exceptions, the one-retry rule, the `errors` ledger, one `aiohttp` session across ten leagues, Brotli bodies | offline |
| `test_nairabet_parity.py` | The Altenar join that builds Nairabet rows from one `GetEvents` body | offline |
| `test_normalizer.py` | Team and league name normalisation and the cached lookup tables | offline |
| `test_betking_empty_body.py` | A Betking league with zero events yields an empty list, not an error | offline |
| `test_surface.py` | The public names of the package; removed names stay removed; the stubs raise `NotImplementedError` | offline |
| `test_endpoint_provenance.py` | Every host the package calls has an entry in `fixtures/endpoint-provenance.json`; no `.har` is tracked | offline |
| `test_charter_scenario.py` | The seven-step user scenario against the stub | offline |
| `test_check_live_run.py` | `scripts/check_live_run.py`, the validator of the release override record | offline |
| `test_docs.py` | The documents match the code: one heading per exception class, the reference example executes against the stub, the README sample and names, the git-cliff version | offline |
| `test_betking_playwright_start.py` | `BetkingPlaywright` starts a browser against a stub page | offline (needs a Chromium build) |
| `e2e/test_gate_fails_closed.py` | The live assertion fails on zero rows and on a blocked league; the default run collects no live test | offline |
| `e2e/test_live_rows.py` | One test per bookmaker against the live site | live |
| `test_betking_playwright.py` | `BetkingPlaywright` against the live Betking site | live |

Fixtures live in `conftest.py`: `stub` (a concrete bookmaker pointed at the stub server), `league_routes` (per-league bodies, status sequences), `blackhole` (a socket that never answers), `closed_port`, `no_retry_sleep`, and the canned payloads under `fixtures/`.

## Running the tests

Offline suite, the same command CI runs:

```bash
uv run pytest tests/ -q --timeout=120 -o log_cli=0 --cov=NaijaBet_Api
```

`make test` runs the same command. The `live_site` marker is deselected by default through `addopts` in `pyproject.toml`, so this command collects no live test.

Live suite (connect Windscribe to Lagos first):

```bash
make live
```

`make live` passes `-m live_site` (a later `-m` overrides the default) and `--live-record live-run.json`; the record holds the egress, the row count per bookmaker, the commit, and the result. `docs/runbooks/live-suite.md` describes the record and the release override.

One bookmaker of the live suite:

```bash
uv run pytest tests/e2e -m live_site -k bet9ja -v
```

## The live assertion

`e2e/gate.py` holds `assert_live_rows(bookmaker)`. It calls `get_all()` and fails when any league raised `BookmakerBlockedError` (the message names the leagues and the wall) or when the ten leagues together returned zero rows; it then checks the eleven keys on the first row and returns the row count. `e2e/test_live_rows.py` calls it for Bet9ja, Betking, and Nairabet and stashes the counts for the record. `e2e/test_gate_fails_closed.py` calls the same function offline against patched bookmakers, so a regression that lets the suite pass on empty data fails offline.

A league that lists no fixtures raises nothing and is tolerated. A failure never returns an empty list; it raises one of the classes in `docs/reference/exceptions.md`.

## The stub

`pytest-httpserver` binds to `127.0.0.1` (not `localhost`, which resolves to `::1` first on Windows and costs about two seconds per request). The `stub` fixture points the Bet9ja league template and the warm-up root at the server. `league_routes.serve(status=..., body=..., sequence=[(status, body), ...])` registers one route per league; a sequence answers in order and repeats its last pair.

## Dependencies

The dev group in `pyproject.toml` installs them: `pytest`, `pytest-asyncio`, `pytest-timeout`, `pytest-httpserver`, `pytest-cov`, `brotli`, and `playwright`. Install with `uv sync --group dev`; add `uv run playwright install chromium` for the browser tests.
