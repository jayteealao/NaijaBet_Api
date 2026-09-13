from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("NaijaBet_Api")
except PackageNotFoundError:  # pragma: no cover - source checkout without an installed distribution
    __version__ = "0.0.0"
