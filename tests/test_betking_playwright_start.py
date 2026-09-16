"""The browser start logs the real status of the front page instead of an unconditional success line."""

import logging

import pytest

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
