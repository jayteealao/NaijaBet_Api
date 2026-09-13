# Runbook: live-site-test-failure

## When this fires

CI logs matching any of the following patterns trigger this runbook:

- `ConnectionError`
- `ReadTimeout`
- `Timeout >120`
- `test_.*_e2e`
- `ConnectTimeout`

## Steps

1. Open the bookmaker site named in the failing test in a browser. Confirm whether the site responds.
2. Re-run the failed job once.
3. When the site is down and the job fails again, record the skipped test in the release record.
4. Continue the release only after a human go.

## Notes

The end-to-end tests call the live Bet9ja, Betking, and Nairabet sites. A failure can mean the site is down, not that the code is wrong.

_Last reviewed: 2026-09-13._
