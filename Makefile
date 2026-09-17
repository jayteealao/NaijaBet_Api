# Developer tasks. Run `make setup` once after cloning.
SHELL := /bin/bash
.DEFAULT_GOAL := help

PACKAGE := NaijaBet_Api
PYTEST_ARGS := tests/ -q --timeout=120 -o log_cli=0
LIVE_ARGS := tests/ -q --timeout=300 -o log_cli=0 -m live_site
# Local egress lanes read WG_CONF_PATH and BRIGHTDATA_PROXY_URL from this gitignored file.
ENV_FILE ?= .env.live
LAGOS_IMAGE ?= naijabet-lagos
# CMD reaches the container through the environment, verbatim; a shell line with && or quotes stays whole.
export CMD

.PHONY: help setup check format lint type-check test live lagos live-wg live-proxy build release-pr tag clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-12s %s\n", $$1, $$2}'

setup: ## Install the project, the dev tools, and the git hooks
	uv sync --group dev
	uv run pre-commit install --install-hooks

check: format lint type-check test ## Run every pre-merge gate locally

format: ## Check formatting
	uv run ruff format --check .

lint: ## Lint
	uv run ruff check .

type-check: ## Type-check the package
	uv run ty check $(PACKAGE)

test: ## Run the test suite with coverage
	uv run pytest $(PYTEST_ARGS) --cov=$(PACKAGE)

live: ## Run the live suite against the bookmakers and write live-run.json (connect the Lagos VPN first)
	unset LIVE_EXPECT; uv run pytest $(LIVE_ARGS) --live-record live-run.json

lagos: ## Run CMD="..." inside a container tunnelled to Lagos over WireGuard (Docker Desktop and WG_CONF_PATH in .env.live)
	@set -euo pipefail; set -a; . $(ENV_FILE); set +a; \
	WG_CONF_PATH="$${WG_CONF_PATH%$$'\r'}"; \
	test -n "$$CMD" || { echo 'usage: make lagos CMD="<shell line>"'; exit 2; }; \
	test -n "$$WG_CONF_PATH" || { echo "WG_CONF_PATH is not set in $(ENV_FILE)"; exit 2; }; \
	test -r "$$WG_CONF_PATH" || { echo "WG_CONF_PATH does not point at a readable file"; exit 2; }; \
	DOCKER_BUILDKIT=1 docker build -q -f docker/lagos.Dockerfile -t $(LAGOS_IMAGE) . >/dev/null; \
	MSYS_NO_PATHCONV=1 docker run --rm --cap-add NET_ADMIN --device /dev/net/tun \
	  --sysctl net.ipv4.conf.all.src_valid_mark=1 -e LIVE_EXPECT -e CMD \
	  -v "$$(pwd -W 2>/dev/null || pwd):/work" -v "$$WG_CONF_PATH:/run/wg/source.conf:ro" \
	  $(LAGOS_IMAGE)

live-wg: ## Run the live suite inside the Lagos container (all three bookmakers) and write live-run.json
	@$(MAKE) --no-print-directory lagos CMD="make live"

live-proxy: ## Run the live suite through BRIGHTDATA_PROXY_URL in .env.live (Betking and Nairabet; Bet9ja reported)
	@set -euo pipefail; set -a; . $(ENV_FILE); set +a; \
	BRIGHTDATA_PROXY_URL="$${BRIGHTDATA_PROXY_URL%$$'\r'}"; \
	test -n "$$BRIGHTDATA_PROXY_URL" || { echo "BRIGHTDATA_PROXY_URL is not set in $(ENV_FILE)"; exit 2; }; \
	HTTPS_PROXY="$$BRIGHTDATA_PROXY_URL" HTTP_PROXY="$$BRIGHTDATA_PROXY_URL" LIVE_EXPECT=betking,nairabet \
	  uv run pytest $(LIVE_ARGS) --ignore=tests/test_betking_playwright.py --live-record live-run-proxy.json

build: ## Build the wheel and sdist and check them
	rm -rf dist/
	uv run python -m build
	uv run twine check dist/*

release-pr: ## Compute the next version from conventional commits, update pyproject.toml and CHANGELOG.md, open the release PR
	@set -euo pipefail; \
	VERSION="$$(git cliff --bumped-version | sed 's/^v//')"; \
	echo "Next version: $$VERSION"; \
	git switch -c "release/v$$VERSION"; \
	sed -i -E "0,/^version = \".*\"/s//version = \"$$VERSION\"/" pyproject.toml; \
	git cliff --tag "v$$VERSION" -o CHANGELOG.md; \
	git add pyproject.toml CHANGELOG.md; \
	git commit -m "chore(release): v$$VERSION"; \
	git push -u origin "release/v$$VERSION"; \
	gh pr create --base main --title "chore(release): v$$VERSION" --body "Release v$$VERSION. After this pull request merges, run: make tag"

tag: ## Tag the current main with the pyproject.toml version and push the tag (starts the release workflow)
	@set -euo pipefail; \
	git switch main && git pull --ff-only; \
	VERSION="$$(uv run python -c 'import tomllib; print(tomllib.load(open("pyproject.toml", "rb"))["project"]["version"])')"; \
	git tag -a "v$$VERSION" -m "v$$VERSION"; \
	git push origin "v$$VERSION"; \
	echo "Pushed v$$VERSION. Watch: gh run watch"

clean: ## Remove build output
	rm -rf dist/ build/ *.egg-info .smoke .coverage
