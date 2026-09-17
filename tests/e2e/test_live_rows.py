"""Each expected bookmaker returns at least one row across its ten leagues; the others are reported."""

import pytest

from NaijaBet_Api.bookmakers import Bet9ja, Betking, Nairabet
from tests.conftest import COUNTS, REPORTED
from tests.e2e.gate import assert_live_rows, collect, expected_bookmakers, report_blocked

pytestmark = [pytest.mark.live_site, pytest.mark.timeout(300)]


@pytest.mark.parametrize("cls", [Bet9ja, Betking, Nairabet], ids=lambda cls: cls.__name__.lower())
def test_bookmaker_returns_rows(cls, request):
    bookmaker = cls()

    if bookmaker.site in expected_bookmakers():
        count = assert_live_rows(bookmaker)
        request.config.stash.setdefault(COUNTS, {})[bookmaker.site] = count
    else:
        rows, errors = collect(bookmaker)
        report = {"rows": len(rows), **report_blocked(bookmaker.site, errors)}
        request.config.stash.setdefault(REPORTED, {})[bookmaker.site] = report
