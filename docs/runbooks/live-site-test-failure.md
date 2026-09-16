# Runbook: live-site-test-failure

## When this fires

CI logs matching any of the following patterns trigger this runbook:

- `BookmakerBlockedError`
- `BookmakerUnreachableError`
- `BookmakerTimeoutError`
- `egress country=`
- `zero rows across`
- `WINDSCRIBE_WG_CONF is empty`

## Steps

1. Open the live job log. When the line `egress country=` does not show `NG` and `200`, the tunnel failed; regenerate the Windscribe config and re-set the secret per [live-suite.md](live-suite.md).
2. Re-run the failed job once.
3. When the job fails again and the bookmaker answers in a browser from Lagos, run `make live` from Lagos and submit the record per [live-suite.md](live-suite.md).
4. Continue the release only after a human go.

## Notes

The live suite (`tests/e2e/`) calls the live Bet9ja, Betking, and Nairabet sites from a WireGuard tunnel to a Lagos exit. A failure can mean the tunnel or the exit failed, not that the code is wrong.

_Last reviewed: 2026-09-16._
