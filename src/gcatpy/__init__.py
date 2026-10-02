"""gcatpy: a Python API for McDowell's General Catalog of Artificial Space Objects.

GCAT data are by Jonathan McDowell and licensed under CC BY 4.0
(https://creativecommons.org/licenses/by/4.0/). Cite as:
McDowell, J., 2020: General Catalog of Artificial Space Objects,
https://planet4589.org/space/gcat

Attributes:
    __version__: Installed distribution version of gcatpy, or ``"0.0.0+unknown"``
        when the package is imported without installed metadata (for example via
        ``PYTHONPATH=src`` or a frozen application).
"""

from importlib.metadata import PackageNotFoundError, version

from gcatpy.hello import greet

__all__ = ["__version__", "greet"]

_UNKNOWN_VERSION = "0.0.0+unknown"

try:
    __version__: str = version("gcatpy")
except PackageNotFoundError:
    # Not installed (source-tree import, vendored copy, or frozen app without metadata).
    # Importing the library must not fail just because the version is unavailable.
    __version__ = _UNKNOWN_VERSION
