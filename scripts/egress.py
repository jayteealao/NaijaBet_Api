"""The current egress as ipinfo sees it; shared by the recording script and the live suite."""

from __future__ import annotations

import requests


def egress() -> dict:
    """Return ipinfo's view of the current egress: ip, city, country, org."""
    response = requests.get("https://ipinfo.io/json", timeout=(10, 30))
    response.raise_for_status()
    info = response.json()
    return {key: info.get(key) for key in ("ip", "city", "country", "org")}
