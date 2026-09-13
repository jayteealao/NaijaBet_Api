# Changelog

## 0.3.0 — 2026-09-13

Python 3.10 or later is required. Installation on Python 3.8 or 3.9 now fails.

The pinned dependency set moved to current releases. This resolves 61 known security advisories across aiohttp, certifi, idna, requests, and urllib3.

- aiohttp: 3.7.4.post0 → 3.14.3
- requests: 2.26.0 → 2.34.2
- urllib3: 1.26.6 → 2.7.0
- certifi: 2021.5.30 → 2026.7.22
- idna: 3.2 → 3.19

The release workflow builds on Python 3.12.
