# Runbook: live-suite

## What the live suite is

`tests/e2e/test_live_rows.py` calls `get_all()` on Bet9ja, Betking, and Nairabet. One bookmaker fails when any league raised `BookmakerBlockedError` or when the ten leagues together returned zero rows; the assertion lives in `tests/e2e/gate.py`. The tests carry the `live_site` marker and are deselected by default (`addopts` in `pyproject.toml`), so `pytest` and `make test` stay offline.

The suite runs in three places:

- `.github/workflows/live.yml`, weekly on Monday 06:00 UTC and on `workflow_dispatch`, from a WireGuard tunnel to a Windscribe Lagos exit.
- `.github/workflows/release.yml`, which calls `live.yml` before the `build` job. A failed or skipped live job blocks the release.
- `make live` on a maintainer machine connected to Windscribe Lagos.

The bookmakers answer only a Nigerian egress. The job proves the egress before the suite runs: `curl https://ipinfo.io/country` must print `NG`, and `https://sports.bet9ja.com/` must answer 200 to a browser User-Agent. The job log shows the line `egress country=NG bet9ja=200`.

## Create the tunnel secret

The tunnel config is the repository secret `WINDSCRIBE_WG_CONF`. Its content is a WireGuard config file that carries the private key, so it never goes into a chat, a log, a commit, or an issue.

1. Open Windscribe: My Account → Config Generators → WireGuard.
2. Select Nigeria, Lagos, and generate a key. Download the `.conf` file.
3. Set the secret from the file. On PowerShell:
   ```powershell
   Get-Content -Raw .\Windscribe-Lagos.conf | gh secret set WINDSCRIBE_WG_CONF
   ```
   On a POSIX shell:
   ```bash
   gh secret set WINDSCRIBE_WG_CONF < Windscribe-Lagos.conf
   ```
4. Delete the local `.conf` file, or keep it outside the repository.
5. Run `gh workflow run live.yml --ref main` and `gh run watch`. The job must print `egress country=NG bet9ja=200` and pass 12 tests.

The job strips the `DNS =` line and the `::/0` route from the config before `wg-quick up`; the runner has no `resolvconf` and no IPv6 route. Keep the exported file as Windscribe wrote it.

## Run the live suite locally

1. Connect Windscribe to Lagos.
2. Run the suite:
   ```bash
   make live
   ```
   Expected: `12 passed, 1 skipped` (the skipped test runs only when Playwright is absent) in under five minutes, and a new `live-run.json` in the repository root.
3. Check the record:
   ```bash
   uv run python scripts/check_live_run.py live-run.json
   ```
   Expected: `live-run.json accepted: ran-at <timestamp>, bet9ja=<n>, betking=<n>, nairabet=<n>` and exit 0.

`live-run.json` holds `ran-at` (UTC), `egress` (ip, city, country, org from ipinfo), `bookmakers` (row count per bookmaker), `git-sha`, and `passed`. The file is gitignored.

To run one bookmaker:

```bash
uv run pytest tests/e2e -m live_site -k bet9ja -v
```

## Submit an override record

The override is for one case: the live job in the release run failed for an egress reason (the tunnel did not come up, the exit is not in Nigeria, a bookmaker denies the exit) while the bookmakers answer from a maintainer's Lagos connection. It is not for a bookmaker outage and not for a failing assertion.

Conditions the workflow enforces (`scripts/check_live_run.py`):

- `ran-at` is at most 7 days old and carries a timezone;
- `bookmakers` has an integer above zero for `bet9ja`, `betking`, and `nairabet`;
- `passed` is `true`;
- `git-sha` is present.

1. Run `make live` from Lagos and check the record (previous section).
2. Confirm the tag exists on `main`: `git tag --list vX.Y.Z`.
3. Dispatch the release with the record:
   ```bash
   gh workflow run release.yml --ref main -f tag=vX.Y.Z -F live-run-json=@live-run.json
   ```
   The `live` job is skipped; the `check-override` job validates the record and prints the accepted line; `build` runs when `test` and `check-override` passed.
4. Record the run URL and the reason for the override in the release notes.

## Read the live job

1. Open the run: `gh run list --workflow live.yml --limit 5`, then `gh run view <id> --log`.
2. Read the step "Bring up the tunnel". `WINDSCRIBE_WG_CONF is empty` means the secret is missing. A `wg-quick` error means the config did not apply; regenerate it in Windscribe.
3. Read the step "Prove the egress". `egress country=NG bet9ja=200` is the pass line. A country other than `NG` means the exit is not in Nigeria; regenerate the config for Lagos. `bet9ja=403` means Bet9ja denies the exit; regenerate the key to get a new exit address, then rerun.
4. Read the step "Live suite". An assertion names the bookmaker and the cause: `<site>: blocked on ['<LEAGUE>', ...]` or `<site>: zero rows across 10 leagues`.
5. Download the record: `gh run download <id> -n live-run`.

`gh run view --log` shows the latest attempt only; an earlier attempt is at `gh api repos/{owner}/{repo}/actions/runs/<id>/attempts/1/logs`.

## Rotate the key

The ship plan treats a secret older than 90 days as stale. Rotate before day 90:

1. Generate a new WireGuard key for Lagos in Windscribe (the previous section "Create the tunnel secret", steps 1 to 3).
2. Run `gh workflow run live.yml --ref main` and confirm the pass line.
3. Delete the old key in Windscribe's config generator.

## Notes

The live suite proves the egress and the endpoints, not the odds values. A bookmaker that lists no fixtures for one league raises nothing and stays tolerated; the assertion fails only when a bookmaker returns zero rows across all ten leagues.

_Last reviewed: 2026-09-16._
