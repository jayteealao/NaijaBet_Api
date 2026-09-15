from importlib.metadata import PackageNotFoundError, version

from NaijaBet_Api.exceptions import (
    BookmakerBlockedError,
    BookmakerTimeoutError,
    BookmakerUnreachableError,
    NaijaBetError,
    ResponseParseError,
)

try:
    __version__ = version("NaijaBet_Api")
except PackageNotFoundError:  # pragma: no cover - source checkout without an installed distribution
    __version__ = "0.0.0"

__all__ = [
    "__version__",
    "NaijaBetError",
    "BookmakerBlockedError",
    "BookmakerUnreachableError",
    "BookmakerTimeoutError",
    "ResponseParseError",
]
