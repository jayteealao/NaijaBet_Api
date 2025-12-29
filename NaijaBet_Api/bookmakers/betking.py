from NaijaBet_Api.bookmakers.BaseClass import BookmakerBaseClass
from NaijaBet_Api.utils.normalizer import betking_match_normalizer
from NaijaBet_Api.utils import jsonpaths

"""
[summary]
"""


class Betking(BookmakerBaseClass):
    """
     This class provides access to https://betking.com/sports 's odds data.

     it provides a variety of methods to query the endpoints and obtain
     odds data at a competiton and match level.

    Attributes:
        session: holds a requests session object for the class as a static variable.
    """

    _site = 'betking'
    _url = "https://betking.com/sports/s"
    _headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": "https://betking.com/",
        "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
    }


    def normalizer(self, args):
        return betking_match_normalizer(jsonpaths.betking_validator(args))
