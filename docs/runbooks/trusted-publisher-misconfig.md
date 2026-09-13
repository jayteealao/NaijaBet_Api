# Runbook: trusted-publisher-misconfig

## When this fires

CI logs matching any of the following patterns trigger this runbook:

- `invalid-publisher`
- `OIDC`
- `id-token`
- `Trusted publishing exchange failure`

## Steps

1. Open the Publishing page of the project on pypi.org and on test.pypi.org.
2. Confirm the publisher row matches owner `jayteealao`, repository `NaijaBet_Api`, workflow `release.yml`, and the environment name of the failing job (`pypi` or `test-pypi`).
3. Confirm the failing job declares `permissions: id-token: write`.
4. Re-run the failed job.

## Notes

_Last reviewed: 2026-09-13._
