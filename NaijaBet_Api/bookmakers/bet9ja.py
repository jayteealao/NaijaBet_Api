from NaijaBet_Api.utils.normalizer import bet9ja_match_normalizer
import requests
from NaijaBet_Api.id import Betid
from NaijaBet_Api.utils import jsonpaths

"""
[summary]
"""


class Bet9ja:
    """
     This class provides access to https://sports.bet9ja.com 's odds data.

     it provides a variety of methods to query the endpoints and obtain
     odds data at a competiton and match level.

    Attributes:
        session: holds a requests session object for the class as a static variable.
    """

    session = requests.Session()
    session.get("https://sports.bet9ja.com")

    def __init__(self) -> None:
        """
        Inits the class
        """
        self.site = "bet9ja"

    def get_nations(self, nation: str):

        pass

    def get_competitions():
        pass

    def get_team(self, team):
        self.get_all()

        def filter_func(data):
            match: str = data["match"]
            return match.lower().find(team.lower()) != -1

        return list(filter(filter_func, self.data))

    def get_league(self, league: Betid = Betid.PREMIERLEAGUE):
        """
        Provides access to available league level odds for unplayed matches

        Returns:
            [type]: [description]
        """
        try:
            res = Bet9ja.session.get(url=league.to_endpoint(self.site))
            # print(res.status_code)
        except Exception as e:
            print(e)
            return {}
        else:
            self.rawdata = res.json()
        if self.rawdata["R"] == "OK":
            self.data = bet9ja_match_normalizer(jsonpaths.bet9ja_validator(self.rawdata))
            # self.data = jsonpaths.bet9ja_validator(self.rawdata)
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
