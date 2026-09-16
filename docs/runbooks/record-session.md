# Runbook: record-session

## When to record

Record a session when a bookmaker host or path in `NaijaBet_Api/id.py` or `NaijaBet_Api/utils/altenar.py` changes, or when `tests/test_endpoint_provenance.py` fails with an unrecorded host. The manifest `tests/fixtures/endpoint-provenance.json` is the evidence that every host the package calls was observed from a browser on a Nigerian egress; the test compares the package's hosts with the manifest and the library's Premier League URL with the recorded sample URL.

## Run the recorder

The recorder needs the `playwright` extra and a Chromium build:

```bash
pip install "NaijaBet_Api[playwright]"
playwright install chromium
```

1. Connect Windscribe to Lagos. The recorder checks `https://ipinfo.io/json` and exits when the country is not `NG`; `--no-egress-check` skips the check for a deliberate non-Nigerian recording.
2. Run the recorder:
   ```bash
   uv run python scripts/record_session.py --out .scratch/recordings/<stamp>
   ```
   `--headed` shows the browser window. Without `--out`, the recorder writes to `.scratch/recordings/<UTC stamp>/`.
3. Read the printed table. One line per recorded request: host, path, status, content type. Each bookmaker's Premier League URL must show status 200; the exit code is 1 otherwise.
4. Read the printed JSON: `recorded-at`, `egress`, `resolved` (host to IP), `premier-league-status` per bookmaker, `cookie-values-redacted` (a count), and the HAR path.

The recorder visits, per bookmaker, the warm-up URL (`_url`) and the exact Premier League URL the library builds, with the library's own headers. The HAR keeps only requests to `bet9ja.com`, `betking.com`, `nairabet.com`, and `biahosted.com` hosts, with response bodies embedded. It writes the decoded Premier League body per bookmaker as `<bookmaker>-premier-league.json` next to the HAR; a body is the source for a canned fixture under `tests/fixtures/` when a payload shape changes.

## Review the manifest entry

Write the manifest entry from the printed facts; the keys differ, so translate rather than copy:

- Top level: `recorded-at` (printed), `egress` with `city`, `country`, `ip` (printed) and `provider` (the printed `org`), `resolver` (how the machine resolved the hosts, for example the system resolver over the Windscribe tunnel), `method` (`playwright-har`), `script` (`scripts/record_session.py`), `recorded-by` (your GitHub login).
- One entry per host under `hosts`: `bookmaker`, `host`, `role` (`site`, `api`, or `referer`), `status` (from the printed table), `resolved-ip` (from the printed `resolved` map), and `sample-url` for an `api` host (the exact Premier League URL from the table).
- Move a host the package stopped calling to `superseded`, with `status`, `checked-at`, and a `note`.

Then run the manifest test:

```bash
uv run pytest tests/test_endpoint_provenance.py -q
```

Expected: every package host has a manifest entry, the Nairabet `api` host is not `sports-api.nairabet.com`, and each bookmaker's library URL equals the recorded `sample-url`.

## Redact and store the HAR

The recorder replaces every cookie value and every `cookie` and `set-cookie` header value with `REDACTED` before it writes `session.har`. Before the HAR leaves the machine, check the other headers by hand: an `authorization` header or a token in a query string needs the same treatment.

The HAR is never committed: `.gitignore` lists `*.har` and `.scratch/`, and `tests/test_endpoint_provenance.py` fails when a tracked `.har` file exists. Keep the HAR outside the repository, or delete it after the manifest is updated. The manifest carries the facts; the HAR is the working file.

## Notes

The recording proves what the browser saw on one date from one egress. A bookmaker can move a host without notice; the weekly live workflow fails before the next release: every league of that bookmaker fails, `get_all` raises `NaijaBetError`, and the live test names the bookmaker.

_Last reviewed: 2026-09-16._
