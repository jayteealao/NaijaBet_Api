# Live evidence

This document records what the live suite proved, when, and from where. The procedure for running the suite and for the release override is in [docs/runbooks/live-suite.md](docs/runbooks/live-suite.md).

## What the live suite proves

`tests/e2e/test_live_rows.py` calls `get_all()` on each of Bet9ja, Betking, and Nairabet. For one bookmaker the test passes only when:

- no league raised `BookmakerBlockedError` (a 403, a Cloudflare challenge, or an Akamai denial fails the test; the message names the leagues and the wall);
- the ten leagues together returned at least one row;
- the first row carries the eleven keys (`match`, `league`, `time`, `league_id`, `match_id`, `home`, `draw`, `away`, `home_or_draw`, `home_or_away`, `draw_or_away`).

The assertion is `assert_live_rows` in `tests/e2e/gate.py`. `tests/e2e/test_gate_fails_closed.py` runs the same assertion offline against a bookmaker patched to return zero rows and against one patched to raise a block; both fail and name the bookmaker. The live suite is therefore not able to pass on empty data.

The suite carries the `live_site` marker and is deselected by default; `make live` runs it and writes `live-run.json`.

## Endpoints

The hosts come from a browser session recorded on 2026-09-15 from Lagos (`tests/fixtures/endpoint-provenance.json`; the recorder is `scripts/record_session.py`, see [docs/runbooks/record-session.md](docs/runbooks/record-session.md)). `tests/test_endpoint_provenance.py` fails when the package calls a host the manifest does not record.

| Bookmaker | API host | Premier League sample | Status on 2026-09-15 |
|---|---|---|---|
| Bet9ja | `sports.bet9ja.com` | `/desktop/feapi/PalimpsestAjax/GetEventsInGroupV2?GROUPID=170880&DISP=0&GROUPMARKETID=1&matches=true` | 200 |
| Betking | `sportsapicdn-desktop.betking.com` | `/api/feeds/prematch/en/4/20000841/0/0` | 200 |
| Nairabet | `sb2frontend-altenar2.biahosted.com` (Altenar widget API) | `/api/widget/GetEvents?...&integration=nairabet&...&champIds=2936` | 200 |

The former Nairabet host `sports-api.nairabet.com` has no DNS record; the manifest lists it under `superseded`.

## Latest recorded run

CI run [35125895143](https://github.com/jayteealao/NaijaBet_Api/actions/runs/35125895143), workflow `live.yml`, 2026-09-16T17:04Z, commit `df3e88b`:

- egress proof: `egress country=NG bet9ja=200` (WireGuard tunnel to a Windscribe Lagos exit, `79.127.149.9`, AS212238 Datacamp Limited);
- result: `12 passed, 1 skipped, 84 deselected in 177.81s`;
- `live-run.json` (uploaded as the `live-run` artifact):

```json
{
  "ran-at": "2026-09-16T17:08:06+00:00",
  "egress": { "ip": "79.127.149.9", "city": "Lagos", "country": "NG", "org": "AS212238 Datacamp Limited" },
  "bookmakers": { "bet9ja": 144, "betking": 144, "nairabet": 134 },
  "git-sha": "df3e88b77950f92ac62cb08aebb4d82db1bc11c5",
  "passed": true
}
```

A maintainer run of `make live` from Windscribe Lagos on 2026-09-16T16:42Z (`79.127.149.6`) passed the same 12 tests in 74.80 s with the same counts: bet9ja 144, betking 144, nairabet 134.

The first attempt of the earlier run 35124398180 ran before the secret existed; it failed at "Bring up the tunnel" with `WINDSCRIBE_WG_CONF is empty` and skipped the suite, which is the designed fail-closed behaviour.

## Sample row

One Bet9ja row from the Lagos run of 2026-09-16 (`time` is epoch seconds):

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

## Reproduce

1. Connect Windscribe to Lagos.
2. Run `make live`. Expected: `12 passed, 1 skipped` and a new `live-run.json`.
3. Run `uv run python scripts/check_live_run.py live-run.json`. Expected: `live-run.json accepted: ...` and exit 0.

The `live` workflow also runs every Monday at 06:00 UTC; the latest runs are at [actions/workflows/live.yml](https://github.com/jayteealao/NaijaBet_Api/actions/workflows/live.yml). Each release run calls the same workflow before it builds.
