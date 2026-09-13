# Developer tasks. Run `make setup` once after cloning.
SHELL := /bin/bash
.DEFAULT_GOAL := help

PACKAGE := NaijaBet_Api
PYTEST_ARGS := tests/ -q --timeout=120 -o log_cli=0 --ignore=tests/test_betking_playwright.py

.PHONY: help setup check format lint type-check test build release-pr tag clean

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
