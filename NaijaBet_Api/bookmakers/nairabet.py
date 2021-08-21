from NaijaBet_Api.utils.normalizer import nairabet_match_normalizer
import requests
from NaijaBet_Api.id import Betid
from NaijaBet_Api.utils import jsonpaths

"""
[summary]
"""


class Nairabet:
    """
     This class provides access to https://nairabet.com 's odds data.

     it provides a variety of methods to query the endpoints and obtain
     odds data at a competiton and match level.

    Attributes:
        session: holds a requests session object for the class as a static variable.
    """

    session = requests.Session()
    session.get("https://nairabet.com")

    def __init__(self) -> None:
        """
        Inits the class
        """
        self.site = "nairabet"

    def get_nations(self, nation: str):

        pass

    def get_competitions():
        pass

    def get_team(self, team):
        self.get_all()

        def filter_func(data):
            match: str = data["match"]
            if match.lower().find(team.lower()) != -1:
                return True
            return False

        return list(filter(filter_func, self.data))

    def get_league(self, league: Betid = Betid.PREMIERLEAGUE):
        """
        Provides access to available league level odds for unplayed matches

        Returns:
            [type]: [description]
        """
        print(league.to_endpoint(self.site))
        try:
            res = Nairabet.session.get(url=league.to_endpoint(self.site))
            # print(res.status_code)
        except Exception as e:
            print(e)
            return {}
        else:
            self.rawdata = res.json()
            if self.rawdata['code'] == 200:
                self.data = nairabet_match_normalizer(jsonpaths.nairabet_validator(self.rawdata))
                # self.data = jsonpaths.nairabet_validator(self.rawdata)
                return self.data

    def get_all(self):
        """
        provides odds for all 1x2 and doublechance markets for all implemented leagues

        Returns:
            Sequence[Mapping[str, str]]: A lis
        """
        self.data = []
        for league in Betid:
            self.data += self.get_league(league)
        return self.data
