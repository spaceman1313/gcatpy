"""gcatpy: a Python API for Jonathan McDowell's General Catalog of Artificial Space Objects.

GCAT data are by Jonathan McDowell and licensed under CC BY 4.0
(https://creativecommons.org/licenses/by/4.0/). Cite as:
McDowell, J., 2020: General Catalog of Artificial Space Objects,
https://planet4589.org/space/gcat

Attributes:
    __version__: Installed distribution version of gcatpy.
"""

from importlib.metadata import version

__all__ = ["__version__"]

__version__: str = version("gcatpy")
