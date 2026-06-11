"""text-file-collector package."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("text-file-collector")
except PackageNotFoundError:
    __version__ = "0.0.0"
