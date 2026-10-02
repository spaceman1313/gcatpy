"""Smoke tests for package import and metadata."""

from importlib.metadata import version

import gcatpy


def test_version_matches_distribution_metadata() -> None:
    """``gcatpy.__version__`` equals the installed distribution version."""
    assert gcatpy.__version__ == version("gcatpy")


def test_package_is_typed() -> None:
    """The PEP 561 ``py.typed`` marker ships with the package."""
    from importlib.resources import files

    assert files("gcatpy").joinpath("py.typed").is_file()
