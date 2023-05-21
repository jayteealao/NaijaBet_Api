from NaijaBet_Api.id import Betid
from NaijaBet_Api.utils.normalizer import nairabet_match_normalizer
from NaijaBet_Api.utils import jsonpaths
from NaijaBet_Api.bookmakers.BaseClass import BookmakerBaseClass

"""
[summary]
"""


class Nairabet(BookmakerBaseClass):
    """
     This class provides access to https://nairabet.com 's odds data.

     it provides a variety of methods to query the endpoints and obtain
     odds data at a competiton and match level.

    Attributes:
        session: holds a requests session object for the class as a static variable.
    """
    _site = 'nairabet'
    _url = "https://nairabet.com"
    _headers = {}

    def normalizer(self, args):
        match = nairabet_match_normalizer(jsonpaths.nairabet_validator(args))
        league = nairabet_match_normalizer(jsonpaths.nairabet_league_validator(args))
        if len(league) > 0:
            print(league)
            print(match)
            for m in match:
                m["league"] = league[0]["league"]
                m["league_id"] = league[0]["league_id"]
        return match
