import asyncio
import json
import logging
import time
import warnings
from abc import ABCMeta, abstractmethod
from typing import Any

import aiohttp
import requests
from aiohttp.http_exceptions import HttpProcessingError
from requests.adapters import HTTPAdapter

from NaijaBet_Api.exceptions import (
    BODY_EXCERPT_CHARS,
    WALL_HTTP,
    BookmakerBlockedError,
    BookmakerTimeoutError,
    BookmakerUnreachableError,
    NaijaBetError,
    ResponseParseError,
    classify_wall,
)
from NaijaBet_Api.id import Betid

logger = logging.getLogger(__name__)

_RETRY_DELAY_S = 1.0
_RETRYABLE_STATUS = range(500, 600)


class _DefaultTimeoutAdapter(HTTPAdapter):
    """Apply a default timeout when a call passes none.

    ``requests.Session`` has no session-level timeout; ``Session.send`` always
    passes ``timeout=None`` explicitly, so the check is for ``None``, not for a
    missing key.
    """

    def __init__(self, timeout: tuple[float, float], **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._timeout = timeout

    def send(self, request, stream=False, timeout=None, verify=True, cert=None, proxies=None):
        if timeout is None:
            timeout = self._timeout
        return super().send(request, stream=stream, timeout=timeout, verify=verify, cert=cert, proxies=proxies)


class BookmakerBaseClass(metaclass=ABCMeta):
    _site: str
    _url: str
    _headers: dict[str, str]

    def __init__(self, session_type: str | None = None, *, timeout: tuple[float, float] = (10, 30)) -> None:
        """Create a bookmaker. No network call happens here.

        Args:
            session_type: Deprecated and ignored; both transports are always available.
            timeout: ``(connect, read)`` seconds applied to every request on both transports.
        """
        if session_type is not None:
            warnings.warn(
                "session_type is deprecated and ignored; both transports are always available",
                DeprecationWarning,
                stacklevel=2,
            )
        self.site = self._site
        self._timeout = timeout
        self._session: requests.Session | None = None
        self._async_session: aiohttp.ClientSession | None = None
        self._warmed = {"sync": False, "async": False}
        self.errors: dict[Betid, NaijaBetError] = {}
        self.data: list[dict] = []

    def __init_subclass__(cls, **kwargs) -> None:
        if not hasattr(cls, "_site") or not hasattr(cls, "_url"):
            raise NotImplementedError
        return super().__init_subclass__(**kwargs)

    # ------------------------------------------------------------------ sessions

    @property
    def request_timeout(self) -> tuple[float, float]:
        """The ``(connect, read)`` timeout in seconds."""
        return self._timeout

    @property
    def session(self) -> requests.Session:
        """The blocking session, created on first access."""
        if self._session is None:
            session = requests.Session()
            adapter = _DefaultTimeoutAdapter(self._timeout)
            session.mount("https://", adapter)
            session.mount("http://", adapter)
            session.headers.update(self._headers)
            self._session = session
        return self._session

    @property
    def async_session(self) -> aiohttp.ClientSession:
        """The aiohttp session, created on first access or after ``aclose()``."""
        if self._async_session is None or self._async_session.closed:
            self._async_session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(sock_connect=self._timeout[0], sock_read=self._timeout[1]),
                headers=self._headers,
            )
            self._warmed["async"] = False
        return self._async_session

    def close(self) -> None:
        """Close the blocking session if one was created."""
        if self._session is not None:
            self._session.close()
            self._session = None
            self._warmed["sync"] = False

    async def aclose(self) -> None:
        """Close the aiohttp session if one was created."""
        if self._async_session is not None and not self._async_session.closed:
            await self._async_session.close()
        self._async_session = None
        self._warmed["async"] = False

    # ------------------------------------------------------------------ fetch path

    def _warm_sync(self) -> None:
        if self._warmed["sync"]:
            return
        try:
            self.session.get(self._url)
        except requests.RequestException as exc:
            logger.debug("%s: warm-up request failed: %s", self.site, exc)
        self._warmed["sync"] = True

    async def _warm_async(self, session: aiohttp.ClientSession) -> None:
        if self._warmed["async"]:
            return
        try:
            async with session.get(self._url):
                pass
        except (aiohttp.ClientError, asyncio.TimeoutError, TimeoutError) as exc:
            logger.debug("%s: warm-up request failed: %s", self.site, exc)
        self._warmed["async"] = True

    def _blocked(self, status: int, body: str) -> BookmakerBlockedError:
        return BookmakerBlockedError(self.site, status, classify_wall(status, body), body[:BODY_EXCERPT_CHARS])

    @staticmethod
    def _retryable(status: int, wall: str) -> bool:
        return status in _RETRYABLE_STATUS and wall == WALL_HTTP

    def _fetch_sync(self, url: str) -> str:
        for attempt in (0, 1):
            try:
                res = self.session.get(url)
            except requests.Timeout as exc:
                raise BookmakerTimeoutError(self.site, f"timed out after {self._timeout} s") from exc
            except requests.ConnectionError as exc:
                if attempt == 0:
                    logger.debug("%s: connection error, retrying once: %s", self.site, exc)
                    time.sleep(_RETRY_DELAY_S)
                    continue
                raise BookmakerUnreachableError(self.site, str(exc)) from exc
            except requests.RequestException as exc:
                raise BookmakerUnreachableError(self.site, str(exc)) from exc
            if res.status_code == 200:
                return res.text
            wall = classify_wall(res.status_code, res.text)
            if attempt == 0 and self._retryable(res.status_code, wall):
                logger.debug("%s: HTTP %s, retrying once", self.site, res.status_code)
                time.sleep(_RETRY_DELAY_S)
                continue
            try:
                res.raise_for_status()
            except requests.HTTPError as exc:
                raise self._blocked(res.status_code, res.text) from exc
            raise self._blocked(res.status_code, res.text)
        raise AssertionError("unreachable")  # pragma: no cover

    async def _fetch_async(self, url: str, session: aiohttp.ClientSession) -> str:
        for attempt in (0, 1):
            try:
                async with session.get(url) as resp:
                    status = resp.status
                    body = await resp.text()
            except (aiohttp.ServerTimeoutError, asyncio.TimeoutError, TimeoutError) as exc:
                raise BookmakerTimeoutError(self.site, f"timed out after {self._timeout} s") from exc
            except (aiohttp.ClientPayloadError, HttpProcessingError) as exc:
                raise ResponseParseError(self.site, f"response body could not be decoded: {exc}") from exc
            except aiohttp.ClientConnectionError as exc:
                if attempt == 0:
                    logger.debug("%s: connection error, retrying once: %s", self.site, exc)
                    await asyncio.sleep(_RETRY_DELAY_S)
                    continue
                raise BookmakerUnreachableError(self.site, str(exc)) from exc
            except aiohttp.ClientError as exc:
                raise BookmakerUnreachableError(self.site, str(exc)) from exc
            except RuntimeError as exc:
                if "Session is closed" in str(exc):
                    raise BookmakerUnreachableError(self.site, "aiohttp session is closed") from exc
                raise
            if status == 200:
                return body
            wall = classify_wall(status, body)
            if attempt == 0 and self._retryable(status, wall):
                logger.debug("%s: HTTP %s, retrying once", self.site, status)
                await asyncio.sleep(_RETRY_DELAY_S)
                continue
            raise self._blocked(status, body)
        raise AssertionError("unreachable")  # pragma: no cover

    def _parse(self, text: str) -> list[dict]:
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ResponseParseError(self.site, "response is not JSON") from exc
        try:
            rows = self.normalizer(data)
        except (TypeError, KeyError, ValueError, AttributeError, IndexError) as exc:
            raise ResponseParseError(self.site, "response shape not recognised") from exc
        if not isinstance(rows, list):
            raise ResponseParseError(self.site, "validator path missing from response")
        return rows

    def _all_failed(self) -> NaijaBetError:
        return NaijaBetError(self.site, f"all {len(Betid)} leagues failed; see .errors")

    # ------------------------------------------------------------------ public API

    @abstractmethod
    def normalizer(self, data):
        pass

    def get_nations(self, nation: str):
        raise NotImplementedError("get_nations is not implemented; see the README TODO list")

    def get_competitions(self):
        raise NotImplementedError("get_competitions is not implemented; see the README TODO list")

    def get_team(self, team: str) -> list[dict]:
        rows = self.get_all()
        return [row for row in rows if row["match"].lower().find(team.lower()) != -1]

    def get_league(self, league: Betid = Betid.PREMIERLEAGUE) -> list[dict]:
        """Return the 1X2 and double-chance rows for one league.

        Raises:
            BookmakerBlockedError: the bookmaker answered with a non-200 status.
            BookmakerUnreachableError: no response arrived; its ``BookmakerTimeoutError``
                subclass means the timeout elapsed.
            ResponseParseError: the body is not the expected JSON shape.
        """
        self._warm_sync()
        return self._parse(self._fetch_sync(league.to_endpoint(self.site)))

    def get_all(self) -> list[dict]:
        """Return the rows of every league; failures land in ``self.errors``.

        Raises:
            NaijaBetError: every league failed.
        """
        self.errors = {}
        rows: list[dict] = []
        for league in Betid:
            try:
                rows += self.get_league(league)
            except NaijaBetError as exc:
                logger.warning("%s: %s failed: %s", self.site, league.name, exc)
                self.errors[league] = exc
        if len(self.errors) == len(Betid):
            raise self._all_failed() from next(iter(self.errors.values()))
        self.data = rows
        return rows

    async def async_get_league(
        self, league: Betid = Betid.PREMIERLEAGUE, async_session: aiohttp.ClientSession | None = None
    ) -> list[dict]:
        """Async form of :meth:`get_league`.

        A caller-supplied ``async_session`` is used as given and never closed.
        """
        own = async_session is None
        session = self.async_session if async_session is None else async_session
        if own:
            await self._warm_async(session)
        return self._parse(await self._fetch_async(league.to_endpoint(self.site), session))

    async def async_get_all(self) -> list[dict]:
        """Async form of :meth:`get_all`; the ten leagues run concurrently on one session."""
        self.errors = {}
        results = await asyncio.gather(*[self.async_get_league(league) for league in Betid], return_exceptions=True)
        rows: list[dict] = []
        for league, result in zip(Betid, results):
            if isinstance(result, NaijaBetError):
                logger.warning("%s: %s failed: %s", self.site, league.name, result)
                self.errors[league] = result
            elif isinstance(result, BaseException):
                raise result
            else:
                rows += result
        if len(self.errors) == len(Betid):
            raise self._all_failed() from next(iter(self.errors.values()))
        seen: set[tuple] = set()
        unique: list[dict] = []
        for row in rows:
            key = tuple(sorted(row.items()))
            if key not in seen:
                seen.add(key)
                unique.append(row)
        self.data = unique
        return unique
