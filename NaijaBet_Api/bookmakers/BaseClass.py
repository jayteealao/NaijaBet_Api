from abc import ABCMeta, abstractmethod
import requests
from NaijaBet_Api.id import Betid
import aiohttp
import asyncio


class BookmakerBaseClass(metaclass=ABCMeta):
    _session = requests
    _async_session = aiohttp

    def __init__(self, session_type='blocking') -> None:
        """
        Inits the class
        """
        self.site = self._site
        if session_type == 'blocking':
            self.session = BookmakerBaseClass._session.session()
            self.session.get(self._url)

        else:
            self.launched = False

    def __init_subclass__(cls, **kwargs) -> None:
        if not hasattr(cls, '_site') or not hasattr(cls, '_url'):
            raise NotImplementedError
        return super().__init_subclass__(**kwargs)

    @abstractmethod
    def normalizer(self):
        pass

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
            res = self.session.get(url=league.to_endpoint(self.site))
            # print(res.status_code)
        except Exception as e:
            print(e)
            return {}
        else:
            # self.data = jsonpaths.nairabet_validator(self.rawdata)    
            return self.normalizer(res.json())

    def get_all(self):
        """
        provides odds for all 1x2 and doublechance markets for all implemented leagues

        Returns:
            Sequence[Mapping[str, str]]: A lis
        """
        self.data = []
        for league in Betid:
            if self.data == {}:
                continue
            self.data += self.get_league(league)
        return self.data

    async def launch_async(self):
        self.session = self._async_session.ClientSession(connector_owner=False)
        async with self.session.get(self._url):
            self.launched = True

    async def async_get_league(self, league: Betid = Betid.PREMIERLEAGUE, async_session: aiohttp.ClientSession = None):
        """
        Provides access to available league level odds for unplayed matches

        Returns:
            [type]: [description]
        """
        if not self.launched:
            await self.launch_async()
        if not async_session:
            async_session = self.session
        async with async_session as session:
            try:
                async with session.get(url=league.to_endpoint(self.site)) as resp:
                    return self.normalizer(await resp.json())
                # print(res.status_code)
                # self.data = jsonpaths.bet9ja_validator(self.rawdata)
            except Exception as e:
                print(e)
                return {}

    async def async_get_all(self):
        """
        provides odds for all 1x2 and doublechance markets for all implemented leagues

        Returns:
            Sequence[Mapping[str, str]]: A lis
        """
        if not self.launched:
            await self.launch_async()
            self.launched = True
        work = await asyncio.gather(*[self.async_get_league(league) for league in Betid])
        # test = [league for league in work if league != {}]
        data = []
        for league in work:
            if league == {}:
                continue
            data += league
        return [dict(member) for member in {tuple(match.items()) for match in data}]
