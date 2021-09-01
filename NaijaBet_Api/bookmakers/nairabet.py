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

    def normalizer(self, args):
        return nairabet_match_normalizer(jsonpaths.nairabet_validator(args))
