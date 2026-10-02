"""Smoke tests for package import and metadata."""

import importlib
import importlib.metadata
from collections.abc import Iterator
from importlib.metadata import PackageNotFoundError, version
from importlib.resources import files

import pytest

import gcatpy


@pytest.fixture
def patched_gcatpy(monkeypatch: pytest.MonkeyPatch) -> Iterator[pytest.MonkeyPatch]:
    """Yield ``monkeypatch``; afterwards undo patches and reload ``gcatpy``.

    The undo must precede the reload so the module is restored with real metadata,
    which fixture teardown order alone does not guarantee.
    """
    yield monkeypatch
    monkeypatch.undo()
    importlib.reload(gcatpy)


def test_version_matches_distribution_metadata() -> None:
    """``gcatpy.__version__`` equals the installed distribution version."""
    assert gcatpy.__version__ == version("gcatpy")


def test_version_falls_back_when_metadata_missing(patched_gcatpy: pytest.MonkeyPatch) -> None:
    """Importing without installed metadata yields a placeholder instead of raising."""

    def _missing(distribution_name: str) -> str:
        raise PackageNotFoundError(distribution_name)

    patched_gcatpy.setattr(importlib.metadata, "version", _missing)
    reloaded = importlib.reload(gcatpy)

    assert reloaded.__version__ == "0.0.0+unknown"


def test_version_restored_after_fallback_test() -> None:
    """The fallback test's cleanup leaves the real version in place."""
    assert gcatpy.__version__ == version("gcatpy")


def test_package_is_typed() -> None:
    """The PEP 561 ``py.typed`` marker ships with the package."""
    assert files("gcatpy").joinpath("py.typed").is_file()
