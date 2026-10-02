"""Tests for the placeholder greeting and the ``python -m gcatpy`` entry point."""

import subprocess
import sys

import pytest

import gcatpy
from gcatpy.__main__ import main
from gcatpy.hello import greet


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("world", "Hello, world! (gcatpy)"),
        ("Sputnik", "Hello, Sputnik! (gcatpy)"),
        ("  Vanguard  ", "Hello, Vanguard! (gcatpy)"),
        ("   ", "Hello, world! (gcatpy)"),
        ("", "Hello, world! (gcatpy)"),
    ],
)
def test_greet(name: str, expected: str) -> None:
    """``greet`` strips whitespace and falls back to the default name when blank."""
    assert greet(name) == expected


def test_greet_default() -> None:
    """``greet()`` with no argument greets the world."""
    assert greet() == "Hello, world! (gcatpy)"


def test_greet_reexported_from_package() -> None:
    """``greet`` is available directly as ``gcatpy.greet``."""
    assert gcatpy.greet is greet


def test_main_prints_greeting(capsys: pytest.CaptureFixture[str]) -> None:
    """``main`` prints the greeting for the given name and returns 0."""
    assert main(["Explorer"]) == 0
    assert capsys.readouterr().out == "Hello, Explorer! (gcatpy)\n"


def test_main_version(capsys: pytest.CaptureFixture[str]) -> None:
    """``--version`` prints the package version and exits with status 0."""
    with pytest.raises(SystemExit) as exc_info:
        main(["--version"])
    assert exc_info.value.code == 0
    assert capsys.readouterr().out.strip() == f"python -m gcatpy {gcatpy.__version__}"


def test_module_runs_as_script() -> None:
    """``python -m gcatpy`` runs end to end in a subprocess."""
    result = subprocess.run(
        [sys.executable, "-m", "gcatpy", "Luna"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip() == "Hello, Luna! (gcatpy)"
