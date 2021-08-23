from NaijaBet_Api.bookmakers.BaseClass import BookmakerBaseClass
from NaijaBet_Api.utils.normalizer import betking_match_normalizer
from pprint import pprint
import requests
from NaijaBet_Api.id import Betid
from NaijaBet_Api.utils import jsonpaths
import asyncio
import aiohttp

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

    # session = requests
    # async_session = aiohttp

    # def __init__(self, session_type='blocking') -> None:
    #     """
    #     Inits the class
    #     """
    #     self.site = "betking"
    #     if session_type == 'blocking':
    #         self.session = Betking.session.session()
    #         self.session.get("https://betking.com/sports/s")
    #     else:
    #         self.launched = False

    # def get_nations(self, nation: str):

    #     pass

    # def get_competitions():
    #     pass

    # def get_team(self, team):
    #     pass

    # async def launch_async(self):
    #     self.session = Betking.async_session.ClientSession(connector_owner=False)
    #     await self.session.get("https://betking.com/sports/s")

    # def get_league(self, league: Betid = Betid.PREMIERLEAGUE):
    #     """
    #     Provides access to available league level odds for unplayed matches

    #     Returns:
    #         [type]: [description]
    #     """
    #     print(league.to_endpoint(self.site))
    #     try:
    #         res = Betking.session.get(url=league.to_endpoint(self.site))
    #         print(res.status_code)
    #     except Exception as e:
    #         print(e)
    #         return {}
    #     else:
    #         self.rawdata = res.json()
    #         # print(self.rawdata)
    #         self.data = betking_match_normalizer(jsonpaths.betking_validator(self.rawdata))
    #         # self.data = jsonpaths.betking_validator(self.rawdata)
    #         return self.data
    
    # async def async_get_league(self, league: Betid = Betid.PREMIERLEAGUE, async_session: aiohttp.ClientSession = None):
    #     """
    #     Provides access to available league level odds for unplayed matches

    #     Returns:
    #         [type]: [description]
    #     """
    #     if not self.launched:
    #         await self.launch_async()
    #         self.launched = True
        
    #     if not async_session:
    #         async_session = self.session
        
    #     async with async_session as session:
    #         try:
    #             res = await session.get(url=league.to_endpoint(self.site))
    #             # print(res.status_code)
    #         except Exception as e:
    #             print(e)
    #             return {}
    #         else:
    #             self.data = betking_match_normalizer(jsonpaths.betking_validator(await res.json()))
    #             # self.data = jsonpaths.betking_validator(self.rawdata)
    #             return self.data

    # def get_all(self):
    #     """
    #     provides odds for all 1x2 and doublechance markets for all implemented leagues

    #     Returns:
    #         Sequence[Mapping[str, str]]: A lis
    #     """
    #     self.data = []
    #     for league in Betid:
    #         self.data += self.get_league(league)
    #     return self.data

    # async def async_get_all(self):
    #     """
    #     provides odds for all 1x2 and doublechance markets for all implemented leagues

    #     Returns:
    #         Sequence[Mapping[str, str]]: A lis
    #     """
    #     if not self.launched:
    #         await self.launch_async()
    #         self.launched = True
    #     self.data = []
    #     tasks = []
    #     async with self.session as session:
    #         for league in Betid:
    #             # tasks.append(asyncio.ensure_future(self.async_get_league(league, session)))
    #             tasks.append(self.async_get_league(league, session))
    #         work = await asyncio.gather(*tasks)
    #         for league in work:
    #             self.data += league
    #         self.data = [dict(member) for member in {tuple(match.items()) for match in self.data}]
    #     return self.data

