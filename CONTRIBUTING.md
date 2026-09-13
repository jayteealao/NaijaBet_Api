# Contributing to NaijaBet_Api

## Set up a checkout

1. Install [uv](https://docs.astral.sh/uv/) and `make`.
2. Clone the repository.
3. Run `make setup`. This installs the package, the dev tools, and the git hooks.

`.python-version` pins the interpreter (3.12). The package supports Python 3.10 or later.

## Run the checks

Run `make check` before you push. It runs the format, lint, type-check, and test gates that CI also runs. CI additionally runs `pip-audit`, commit-message linting, and a package-build dry run (`make build`) that `make check` does not cover.

| Gate | Command |
|---|---|
| format | `uv run ruff format --check .` |
| lint | `uv run ruff check .` |
| type-check | `uv run ty check NaijaBet_Api` |
| test | `uv run pytest tests/ -q --timeout=120 -o log_cli=0 --ignore=tests/test_betking_playwright.py --cov=NaijaBet_Api` |

The end-to-end tests call the live bookmaker sites. When a site is down, a test fails without a code change. Re-run once before you look for a code defect.

## Git hooks

`pre-commit` runs on every commit: ruff (fix and format), ty, gitleaks, and whitespace fixes. The `commit-msg` hook rejects a message that does not follow the convention below. The `pre-push` hook runs the fast test subset.

## Commit messages and pull-request titles

Every commit message and every pull-request title follows [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <summary>
```

Allowed types: `feat`, `fix`, `perf`, `docs`, `refactor`, `build`, `ci`, `chore`, `style`, `test`, `revert`. Mark a breaking change with `!` after the type or scope. The release version is computed from these types: `feat` bumps the minor version, `fix` bumps the patch version.

## Pull requests

1. Branch from `main`.
2. Open a pull request against `main`. Fill in the template.
3. Every required check must pass. The branch must be up to date with `main`.
4. Merge with rebase. Squash and merge commits are disabled.

When you change a normalizer file under `NaijaBet_Api/utils/`, say so in the "Normalizer change" section of the pull-request template.

## Release

Before the first release, complete these steps:

1. Register the Trusted Publisher on test.pypi.org for repository workflow `release.yml` and environment `test-pypi`. Register the Trusted Publisher on pypi.org for repository workflow `release.yml` and environment `pypi`.
2. Run `gh variable set SDLC_GATE_TEST_PYPI_PUBLISH --body true`.
3. Run `gh variable set SDLC_GATE_PYPI_PUBLISH --body true`.

Maintainers release from `main`:

1. Run `make release-pr`. It computes the next version from the commits since the last tag, updates `pyproject.toml` and `CHANGELOG.md`, and opens a release pull request.
2. Merge the release pull request.
3. Run `make tag`. The tag starts the release workflow, which publishes to test.pypi.org, verifies the install, waits for the reviewer approval, publishes to pypi.org, and creates the GitHub release. Until both `SDLC_GATE_TEST_PYPI_PUBLISH` and `SDLC_GATE_PYPI_PUBLISH` are set, the tag workflow only tests and builds and it publishes nothing.

Recovery steps for known failures are in `docs/runbooks/`. To yank a bad release, follow `docs/runbooks/bad-release-rollback.md`.
