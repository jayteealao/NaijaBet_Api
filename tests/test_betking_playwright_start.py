"""The browser start logs the real status of the front page instead of an unconditional success line."""

import logging
import time

import pytest
from werkzeug.wrappers import Response

from NaijaBet_Api.bookmakers.betking_playwright import BetkingPlaywright

LOGGER = "NaijaBet_Api.bookmakers.betking_playwright"


@pytest.mark.timeout(120)
def test_start_browser_logs_403_and_no_success_line(httpserver, monkeypatch, caplog):
    httpserver.expect_request("/sports").respond_with_data(
        "<html><body><h1>Access Denied</h1></body></html>", status=403, content_type="text/html"
    )
    monkeypatch.setattr(BetkingPlaywright, "_sports_url", httpserver.url_for("/sports"))
    client = BetkingPlaywright(headless=True, timeout=30000)

    try:
        with caplog.at_level(logging.INFO, logger=LOGGER):
            try:
                client._start_browser()
            except Exception as exc:  # noqa: BLE001 - a missing browser build is an environment gap
                if "Executable doesn't exist" in str(exc):
                    pytest.skip("chromium not installed for this playwright version")
                raise
    finally:
        client._stop_browser()

    messages = [record.getMessage() for record in caplog.records]
    assert any("403" in message for message in messages), messages
    assert not any("Browser session established" in message for message in messages), messages
    assert any(record.levelno == logging.WARNING for record in caplog.records)


@pytest.mark.timeout(120)
def test_start_browser_cleans_up_after_navigation_failure_and_recovers(httpserver):
    """A navigation failure during ``_start_browser`` must not leave a Playwright instance
    running: it should stop what it started and re-raise, so a later ``_start_browser()``
    call in the same process (which starts a fresh ``sync_playwright()``) still works.
    """

    def slow_handler(_request):
        time.sleep(2)
        return Response("<html><body>too slow</body></html>", status=200, content_type="text/html")

    httpserver.expect_request("/slow").respond_with_handler(slow_handler)
    httpserver.expect_request("/fast").respond_with_data(
        "<html><body>ok</body></html>", status=200, content_type="text/html"
    )

    client = BetkingPlaywright(headless=True, timeout=1000)
    client._sports_url = httpserver.url_for("/slow")

    try:
        client._start_browser()
    except Exception as exc:  # noqa: BLE001 - a missing browser build is an environment gap
        if "Executable doesn't exist" in str(exc):
            pytest.skip("chromium not installed for this playwright version")
    else:
        pytest.fail("expected _start_browser() to raise on a navigation that never settles")

    assert client.playwright is None
    assert client.browser is None
    assert client.context is None
    assert client.page is None

    client._sports_url = httpserver.url_for("/fast")
    client.timeout = 30000
    try:
        client._start_browser()
        assert client.playwright is not None
        assert client.browser is not None
        assert client.page is not None
    finally:
        client._stop_browser()
