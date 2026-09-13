import asyncio
from abc import ABCMeta, abstractmethod

import aiohttp
import requests

from NaijaBet_Api.id import Betid


class BookmakerBaseClass(metaclass=ABCMeta):
    _site: str
    _url: str
    _headers: dict[str, str]
    _session = requests
    _async_session = aiohttp
    session: requests.Session | aiohttp.ClientSession | None = None

    def __init__(self, session_type="blocking") -> None:
        """
        Inits the class
        """
        self.site = self._site
        self.launched = False
        if session_type == "blocking":
            self.session = BookmakerBaseClass._session.session()
            self.session.get(self._url, headers=self._headers)

    def __init_subclass__(cls, **kwargs) -> None:
        if not hasattr(cls, "_site") or not hasattr(cls, "_url"):
            raise NotImplementedError
        return super().__init_subclass__(**kwargs)

    @abstractmethod
    def normalizer(self, data):
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
        headers = self._headers
        session = self.session
        if not isinstance(session, requests.Session):
            print(f"Warning: {self.site} has no blocking session; construct with session_type='blocking'")
            return []

        try:
            res = session.get(url=league.to_endpoint(self.site), headers=headers)
            # print(res.status_code)
            if res.status_code != 200:
                print(f"Warning: HTTP {res.status_code} for {self.site}")
                return []
        except Exception as e:
            print(e)
            return []
        else:
            try:
                # self.data = jsonpaths.nairabet_validator(self.rawdata)
                # print(res.json())
                return self.normalizer(res.json())
            except Exception as e:
                print(f"Error parsing JSON for {self.site}: {e}")
                return []

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
        self.session = self._async_session.ClientSession()
        try:
            async with self.session.get(self._url, headers=self._headers):
                self.launched = True
        except Exception as e:
            print(f"Warning during async session launch: {e}")
            self.launched = True

    async def async_get_league(
        self, league: Betid = Betid.PREMIERLEAGUE, async_session: aiohttp.ClientSession | None = None
    ):
        """
        Provides access to available league level odds for unplayed matches

        Returns:
            [type]: [description]
        """
        if not self.launched:
            await self.launch_async()
        if async_session is None:
            if not isinstance(self.session, aiohttp.ClientSession):
                print(f"Warning: {self.site} has no async session; construct with session_type='async'")
                return {}
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
        try:
            work = await asyncio.gather(*[self.async_get_league(league) for league in Betid])
            # test = [league for league in work if league != {}]
            data = []
            for league in work:
                if league == {}:
                    continue
                data += league
            return [dict(member) for member in {tuple(match.items()) for match in data}]
        finally:
            if isinstance(self.session, aiohttp.ClientSession):
                await self.session.close()
