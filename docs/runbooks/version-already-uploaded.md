# Runbook: version-already-uploaded

## When this fires

CI logs matching any of the following patterns trigger this runbook:

- `File already exists`
- `400 Bad Request`
- `already been used`

## Steps

1. Do not delete the tag. Do not delete the release on pypi.org.
2. Run `git cliff --bumped-version` to compute the next version.
3. Commit the version bump with a conventional commit message. `make release-pr` does steps 2 and 3 and opens the pull request.
4. After the pull request merges, run `make tag`. The new `v*` tag on `main` starts the release workflow again.

## Notes

_Last reviewed: 2026-09-13._
