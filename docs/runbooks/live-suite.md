# Runbook: live-suite

## What the live suite is

`tests/e2e/test_live_rows.py` calls `get_all()` on Bet9ja, Betking, and Nairabet. One bookmaker fails when any league raised `BookmakerBlockedError`, when the ten leagues together returned zero rows, or when the first row lacks one of the eleven keys; the assertion lives in `tests/e2e/gate.py`. The tests carry the `live_site` marker and are deselected by default (`addopts` in `pyproject.toml`), so `pytest` and `make test` stay offline.

The suite runs on four triggers:

- `.github/workflows/live.yml`, weekly on Monday 06:00 UTC and on `workflow_dispatch`, from a WireGuard tunnel to a Windscribe Lagos exit.
- `.github/workflows/release.yml`, which calls `live.yml` before the `build` job. A failed or skipped live job blocks the release.
- `.github/workflows/live.yml` on a push that changes the workflow file, `tests/e2e/`, `tests/conftest.py`, or `scripts/egress.py`, so a change to the gate proves itself on its own branch.
- `make live` on a maintainer machine connected to Windscribe Lagos.

The bookmakers answer only a Nigerian egress. The job proves the egress before the suite runs: `curl https://ipinfo.io/country` must print `NG`, and `https://sports.bet9ja.com/` must answer 200 to a browser User-Agent. The job log shows the line `egress country=NG bet9ja=200`.

## Create the tunnel secret

The secret is the repository secret `WINDSCRIBE_WG_CONF`. Its content is the config file, the WireGuard `.conf` that Windscribe generates. The config file carries the private half of the key, so it never goes into a chat, a log, a commit, or an issue.

CAUTION: keep the config file as Windscribe wrote it. The job strips the `DNS =` line and the `::/0` route itself; a hand-edited file can fail `wg-quick up` on the runner.

1. Open Windscribe: My Account → Config Generators → WireGuard.
2. Select Nigeria, Lagos, and generate a key. Download the config file.
3. Set the secret from the config file. On PowerShell:
   ```powershell
   Get-Content -Raw .\Windscribe-Lagos.conf | gh secret set WINDSCRIBE_WG_CONF
   ```
   On a POSIX shell:
   ```bash
   gh secret set WINDSCRIBE_WG_CONF < Windscribe-Lagos.conf
   ```
4. Delete the local config file, or keep it outside the repository.
5. Run `gh workflow run live.yml --ref main` and `gh run watch`. The job must print `egress country=NG bet9ja=200` and pass 15 tests.

## Run the live suite locally

1. Connect Windscribe to Lagos.
2. Run the suite:
   ```bash
   make live
   ```
   Expected: `15 passed` in under five minutes, and a new `live-run.json` in the repository root.
3. Check the record:
   ```bash
   uv run python scripts/check_live_run.py live-run.json
   ```
   Expected: `live-run.json accepted: ran-at <timestamp>, bet9ja=<n>, betking=<n>, nairabet=<n>` and exit 0.

`live-run.json` holds `ran-at` (UTC), `egress` (ip, city, country, org from ipinfo), `bookmakers` and `bookmakers-async` (row count per bookmaker on each path), `expected` (the bookmakers the run had to prove), `reported` (outcomes of bookmakers outside that set), `proxy-in-use`, `git-sha`, and `passed`. The file is gitignored; the copy the workflow uploads as the `live-run` artifact carries `egress.ip: redacted`.

To run one bookmaker:

```bash
uv run pytest tests/e2e -m live_site -k bet9ja -v
```

## Run the live suite locally without the VPN client

Two lanes read a gitignored `.env.live` at the repository root; `.env.live.example` lists the two keys.

1. Copy `.env.live.example` to `.env.live` and fill in the values. Keep the WireGuard config file outside the repository and write its path with forward slashes.
2. Start Docker Desktop.
3. Run the WireGuard lane:
   ```bash
   make live-wg
   ```
   The first run builds the image, which takes several minutes; later runs start in seconds. The output must show `egress country=NG bet9ja=200` and `15 passed` (the 12 tests above plus 3 async tests), and a new `live-run.json` in the repository root.
4. To run any command from Lagos, pass it as `CMD`:
   ```bash
   make lagos CMD="uv run python scripts/egress.py"
   ```
   The container mounts the repository at `/work`; the tunnel is up before the command starts and down after it ends.
5. Without Docker, run the proxy lane:
   ```bash
   make live-proxy
   ```
   The proxy lane proves Betking and Nairabet and writes `live-run-proxy.json`. Bet9ja is driven but not asserted: its status and wall appear under `reported` (Bet9ja denies the proxy's peers). `live-run-proxy.json` carries `expected: ["betking", "nairabet"]` and `check_live_run.py` rejects it, so a proxy run never serves as a release override. The proxy lane skips the browser tests in `tests/test_betking_playwright.py` because Chromium does not read `HTTPS_PROXY`; the WireGuard lane (`make live-wg`) covers them.

`LIVE_EXPECT` (a comma-separated list) is what narrows the expected set; `make live` unsets it, so the CI lane and the WireGuard lane always prove all three bookmakers.

Never paste a value from `.env.live` into a chat, a log, a commit, or an issue. The record stores `proxy-in-use` as `true` or `false`, never the URL.

## Submit an override record

The override is for one case: the live job in the release run failed for an egress reason (the tunnel did not come up, the exit is not in Nigeria, a bookmaker denies the exit) while the bookmakers answer from a maintainer's Lagos connection. It is not for a bookmaker outage and not for a failing assertion.

Conditions the workflow enforces (`scripts/check_live_run.py`):

- `ran-at` is at most 7 days old, carries a timezone, and is not in the future;
- `bookmakers` has an integer above zero for `bet9ja`, `betking`, and `nairabet`;
- the record carries no `egress-error`;
- `egress.country` is `NG`;
- `proxy-in-use` is not `true`; a record from `make live-proxy` is therefore rejected;
- `passed` is `true`;
- `git-sha` is present;
- `git-sha` equals the commit of the released tag;
- when the record carries an `expected` list, it names all three bookmakers.

1. Run `make live` from Lagos and check the record (previous section).
2. Confirm the tag exists on `origin`: `git ls-remote --tags origin vX.Y.Z` prints one line.
3. Dispatch the release with the record:
   ```bash
   gh workflow run release.yml --ref main -f tag=vX.Y.Z -F live-run-json=@live-run.json
   ```
   The `live` job is skipped; the `check-override` job validates the record and prints the accepted line; `build` runs when `test` and `check-override` passed.
4. Record the run URL and the reason for the override in the release notes.

## Read the live job

1. Open the run: `gh run list --workflow live.yml --limit 5`, then `gh run view <id> --log`.
2. Read the step "Bring up the tunnel". `WINDSCRIBE_WG_CONF is empty` means the secret is missing. A `wg-quick` error means the config file did not apply; generate a new config file in Windscribe and set the secret again.
3. Read the step "Prove the egress". `egress country=NG bet9ja=200` is the pass line. A country other than `NG` means the exit is not in Nigeria; generate a new config file for Lagos and set the secret again. `bet9ja=403` means Bet9ja denies the exit; generate a new config file in Windscribe (a new key gives a new exit address), set the secret again, then rerun.
4. Read the step "Live suite". An assertion names the bookmaker and the cause: `<site>: blocked on ['<LEAGUE>', ...]` or `<site>: zero rows across 10 leagues`.
5. Download the record: `gh run download <id> -n live-run`.

`gh run view --log` shows the latest attempt only; an earlier attempt is at `gh api repos/{owner}/{repo}/actions/runs/<id>/attempts/1/logs`.

## Rotate the key

Rotate the key every 90 days. No workflow checks the age of the secret; the maintainer tracks the date.

1. Generate a new config file for Lagos in Windscribe (section "Create the tunnel secret", steps 1 and 2).
2. Set the secret from the new config file (section "Create the tunnel secret", step 3).
3. Run `gh workflow run live.yml --ref main` and confirm the pass line.
4. Delete the old config file in Windscribe's config generator.

## Notes

The live suite proves the egress and the endpoints, not the odds values. A league that lists no fixtures raises nothing and is tolerated. A bookmaker fails when any league raised `BookmakerBlockedError`, when the ten leagues together returned zero rows, or when the first row lacks one of the eleven keys.

_Last reviewed: 2026-09-17._
