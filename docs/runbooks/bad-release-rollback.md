# Runbook: bad-release-rollback

## When this fires

A published release on pypi.org is bad. Examples: it breaks installs, it ships a
critical defect, or it exposes a secret.

## Steps

1. Yank the release by hand on pypi.org. Open the project page. Open release
   `<version>`. Open Options. Select Yank. Give the reason.
2. Run `gh workflow run rollback.yml -f version=<version> -f reason="<reason>"`.
3. Open the workflow run. Read the run summary. The summary confirms that every
   file of the version is yanked. The summary records the rollback.
4. If the bad release exposed a credential (an API key, a token, a password),
   revoke it and issue a new one before you publish the fixed version. A
   yanked release stays installable with an exact version specifier, so the
   leaked value stays usable until it is revoked.
5. Publish the fixed version with a new tag. Follow the steps in
   `version-already-uploaded.md`. Do not reuse the yanked version number.

## Notes

_Last reviewed: 2026-09-13._
