# The Lagos container: the live suite, or any command, behind a WireGuard tunnel.
# Built and run by `make lagos`; see docs/runbooks/live-suite.md.
FROM python:3.12-slim

# uv pinned to the version that wrote uv.lock; PyPI, so no registry login is needed.
RUN pip install --no-cache-dir uv==0.8.13
# wireguard-go is the fallback when the host kernel lacks the WireGuard module (Docker Desktop's
# WSL2 kernel 5.15 has it). procps supplies sysctl for wg-quick.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        wireguard-tools wireguard-go iproute2 procps curl ca-certificates make git \
    && rm -rf /var/lib/apt/lists/* \
    && git config --system --add safe.directory /work

# The venv lives outside /work so the host's .venv (a Windows venv) is never used.
ENV UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_LINK_MODE=copy \
    WG_QUICK_USERSPACE_IMPLEMENTATION=wireguard-go

WORKDIR /work
COPY pyproject.toml uv.lock .python-version ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --group dev --no-install-project
# Chromium: tests/test_betking_playwright.py runs in the live suite, as in CI.
RUN uv run --no-sync playwright install --with-deps chromium

COPY docker/lagos-entry.sh /usr/local/bin/lagos-entry
RUN chmod 755 /usr/local/bin/lagos-entry

ENTRYPOINT ["/usr/local/bin/lagos-entry"]
