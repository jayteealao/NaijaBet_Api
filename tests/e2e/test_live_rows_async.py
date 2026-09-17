"""The async path on a caller session: each expected bookmaker returns rows; the others are reported."""

import aiohttp
import pytest

from NaijaBet_Api.bookmakers import Bet9ja, Betking, Nairabet
from tests.conftest import ASYNC_COUNTS, REPORTED
from tests.e2e.gate import async_collect, check_rows, expected_bookmakers, report_blocked

pytestmark = [pytest.mark.live_site, pytest.mark.timeout(300)]


@pytest.mark.parametrize("cls", [Bet9ja, Betking, Nairabet], ids=lambda cls: cls.__name__.lower())
async def test_bookmaker_returns_rows_async(cls, request):
    bookmaker = cls()

    # trust_env=True honours HTTPS_PROXY, the one thing the library's own session does not do.
    async with aiohttp.ClientSession(trust_env=True, headers=cls._headers) as session:
        rows, errors = await async_collect(bookmaker, session)

    if bookmaker.site in expected_bookmakers():
        count = check_rows(bookmaker.site, rows, errors)
        request.config.stash.setdefault(ASYNC_COUNTS, {})[bookmaker.site] = count
    else:
        report = {"rows": len(rows), **report_blocked(bookmaker.site, errors)}
        request.config.stash.setdefault(REPORTED, {})[f"{bookmaker.site}-async"] = report
