"""Typed failures raised by every bookmaker fetch.

A fetch method returns a list of rows or raises one of these classes. An empty
list means the bookmaker answered with zero fixtures; it never means a failure.
"""

from __future__ import annotations

import html

WALL_CHALLENGE = "challenge"
WALL_DENIED = "denied"
WALL_HTTP = "http"
BODY_EXCERPT_CHARS = 200

__all__ = [
    "NaijaBetError",
    "BookmakerBlockedError",
    "BookmakerUnreachableError",
    "BookmakerTimeoutError",
    "ResponseParseError",
    "classify_wall",
    "WALL_CHALLENGE",
    "WALL_DENIED",
    "WALL_HTTP",
    "BODY_EXCERPT_CHARS",
]


class NaijaBetError(Exception):
    """Base class for every failure a bookmaker call can raise."""

    def __init__(self, bookmaker: str, message: str) -> None:
        super().__init__(bookmaker, message)
        self.bookmaker = bookmaker
        self.message = message

    def __str__(self) -> str:
        return f"{self.bookmaker}: {self.message}"


class BookmakerBlockedError(NaijaBetError):
    """The bookmaker answered with a non-200 status.

    ``wall`` is ``challenge`` for a Cloudflare challenge page, ``denied`` for an
    Akamai access-denied page, and ``http`` for any other status.
    """

    def __init__(self, bookmaker: str, status: int, wall: str, body_excerpt: str = "") -> None:
        super().__init__(bookmaker, f"HTTP {status} ({wall})")
        self.status = status
        self.wall = wall
        self.body_excerpt = body_excerpt


class BookmakerUnreachableError(NaijaBetError):
    """No HTTP response arrived: DNS, connection, or transport failure."""


class BookmakerTimeoutError(BookmakerUnreachableError, TimeoutError):
    """The connect or read timeout elapsed before a response arrived."""

    def __init__(self, bookmaker: str, message: str) -> None:
        NaijaBetError.__init__(self, bookmaker, message)


class ResponseParseError(NaijaBetError):
    """The bookmaker answered 200 but the body is not the expected JSON shape."""


def classify_wall(status: int, body: str) -> str:
    """Name the wall behind a non-200 answer from its status and body.

    Akamai writes its page with HTML entities (``Reference&#32;&#35;18…``), so the
    body is decoded before the substring tests.
    """
    text = html.unescape(body)
    if "Just a moment" in text or "cf-mitigated" in text:
        return WALL_CHALLENGE
    if "Access Denied" in text and "Reference #" in text:
        return WALL_DENIED
    return WALL_HTTP
