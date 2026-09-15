from NaijaBet_Api.bookmakers.BaseClass import BookmakerBaseClass
from NaijaBet_Api.utils.altenar import MENU_URL, rows_from_get_events
from NaijaBet_Api.utils.normalizer import nairabet_match_normalizer

"""
[summary]
"""


class Nairabet(BookmakerBaseClass):
    """
     This class provides access to https://nairabet.com 's odds data.

     Nairabet's sportsbook is an Altenar widget, so the odds come from the widget API
     rather than from nairabet.com itself. The class provides a variety of methods to
     query the endpoints and obtain odds data at a competition and match level.

    Attributes:
        session: holds a requests session object for the class as a static variable.
    """

    _site = "nairabet"
    _url = MENU_URL
    _headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://nairabet.com/",
    }

    def normalizer(self, data):
        return nairabet_match_normalizer(rows_from_get_events(data))
