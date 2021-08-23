from NaijaBet_Api.utils.normalizer import nairabet_match_normalizer
import requests
from NaijaBet_Api.id import Betid
from NaijaBet_Api.utils import jsonpaths
import aiohttp
import asyncio

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

    session = requests
    async_session = aiohttp

    def __init__(self, session_type='blocking') -> None:
        """
        Inits the class
        """
        self.site = "nairabet"
        if session_type == 'blocking':
            self.session = Nairabet.session.session()
            self.session.get("https://nairabet.com")

        else:
            self.launched = False

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
        # print(league.to_endpoint(self.site))
        try:
            res = Nairabet.session.get(url=league.to_endpoint(self.site))
            # print(res.status_code)
        except Exception as e:
            print(e)
            return {}
        else:
            self.rawdata = res.json()
            if self.rawdata['code'] == 200:
                # self.data = jsonpaths.nairabet_validator(self.rawdata)
                return nairabet_match_normalizer(jsonpaths.nairabet_validator(self.rawdata))
    
    async def launch_async(self):
        self.session = Nairabet.async_session.ClientSession(connector_owner=False)
        await self.session.get("https://nairabet.com")

    async def async_get_league(self, league: Betid = Betid.PREMIERLEAGUE, async_session: aiohttp.ClientSession = None):
        """
        Provides access to available league level odds for unplayed matches

        Returns:
            [type]: [description]
        """
        if not self.launched:
            await self.launch_async()
            self.launched = True
        if not async_session:
            async_session = self.session
        async with async_session as session:
            try:
                res = await session.get(url=league.to_endpoint(self.site))
                # print(res.status_code)
            except Exception as e:
                print(e)
                return {}
            else:
                # self.data = jsonpaths.bet9ja_validator(self.rawdata)
                return nairabet_match_normalizer(jsonpaths.nairabet_validator(await res.json()))

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

    async def async_get_all(self):
        """
        provides odds for all 1x2 and doublechance markets for all implemented leagues

        Returns:
            Sequence[Mapping[str, str]]: A lis
        """
        if not self.launched:
            await self.launch_async()
            self.launched = True
        data = []
        tasks = []
        async with self.session as session:
            for league in Betid:
                # tasks.append(asyncio.ensure_future(self.async_get_league(league, session)))
                tasks.append(self.async_get_league(league, session))
            work = await asyncio.gather(*tasks)
            for league in work:
                data += league
        return [dict(member) for member in {tuple(match.items()) for match in data}]
