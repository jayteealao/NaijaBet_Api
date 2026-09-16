"""Each bookmaker returns at least one row across its ten leagues from an accepted egress."""

import pytest

from NaijaBet_Api.bookmakers import Bet9ja, Betking, Nairabet
from tests.conftest import COUNTS
from tests.e2e.gate import assert_live_rows

pytestmark = [pytest.mark.live_site, pytest.mark.timeout(300)]


@pytest.mark.parametrize("cls", [Bet9ja, Betking, Nairabet], ids=lambda cls: cls.__name__.lower())
def test_bookmaker_returns_rows(cls, request):
    bookmaker = cls()

    count = assert_live_rows(bookmaker)

    request.config.stash.setdefault(COUNTS, {})[bookmaker.site] = count
