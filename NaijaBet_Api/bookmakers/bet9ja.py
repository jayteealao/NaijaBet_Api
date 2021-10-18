from NaijaBet_Api.bookmakers.BaseClass import BookmakerBaseClass
from NaijaBet_Api.utils.normalizer import bet9ja_match_normalizer
from NaijaBet_Api.utils import jsonpaths


"""
[summary]
"""


class Bet9ja(BookmakerBaseClass):
    """
     This class provides access to https://sports.bet9ja.com 's odds data.

     it provides a variety of methods to query the endpoints and obtain
     odds data at a competiton and match level.

    Attributes:
        session: holds a requests session object for the class as a static variable.
    """

    _site = 'bet9ja'
    _url = "https://bet9ja.com"
    _headers = {
        "sec-ch-ua": '"Chromium";v="94", "Microsoft Edge";v="94", ";Not A Brand";v="99"',
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Chrome/94.0.4606.81",
        "referer": "https://sports.bet9ja.com",
    }

    def normalizer(self, args):
        return bet9ja_match_normalizer(jsonpaths.bet9ja_validator(args))
