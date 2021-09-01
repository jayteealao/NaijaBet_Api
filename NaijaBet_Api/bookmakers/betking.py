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

    def normalizer(self, args):
        return betking_match_normalizer(jsonpaths.betking_validator(args))
