"""Tests for the public exceptions in ``gcatpy.errors``."""

import ast
import inspect
import re
from pathlib import Path

import pytest

from gcatpy import errors
from gcatpy.errors import (
    CacheEmptyError,
    CacheInterruptedError,
    CacheLockedError,
    GcatpyError,
    NotAGcatpyRootError,
    RootNotFoundError,
)

ROOT = Path(r"D:\gcat\2026-10-12")
"""A Windows-style root, so messages must survive backslashes."""

_ROOT_DIR_LITERAL = re.compile(r"""download\(root_dir=('[^']*'|"[^"]*")\)""")


def test_all_lists_every_exception_class() -> None:
    """``__all__`` names exactly the exception classes defined in the module."""
    defined = {
        name
        for name, obj in vars(errors).items()
        if inspect.isclass(obj)
        and issubclass(obj, BaseException)
        and obj.__module__ == errors.__name__
    }
    assert set(errors.__all__) == defined


@pytest.mark.parametrize("name", errors.__all__)
def test_every_error_derives_from_base(name: str) -> None:
    """Every public exception can be caught as ``GcatpyError``."""
    assert issubclass(getattr(errors, name), GcatpyError)


def test_root_not_found_error() -> None:
    """``RootNotFoundError`` keeps its path and names it in the message."""
    err = RootNotFoundError(ROOT)
    assert err.path == ROOT
    assert str(ROOT) in str(err)
    assert "Check the path" in str(err)


def test_not_a_gcatpy_root_error_for_folder() -> None:
    """By default the message explains the missing marker."""
    err = NotAGcatpyRootError(ROOT)
    assert err.path == ROOT
    assert err.is_file is False
    assert str(ROOT) in str(err)
    assert ".gcatpy-root" in str(err)


def test_not_a_gcatpy_root_error_for_file() -> None:
    """With ``is_file=True`` the message says the path is a file."""
    err = NotAGcatpyRootError(ROOT, is_file=True)
    assert err.is_file is True
    assert str(ROOT) in str(err)
    assert "is a file" in str(err)


def test_cache_locked_error() -> None:
    """``CacheLockedError`` keeps the lock file and names it in the message."""
    lock = ROOT / "cache" / ".lock"
    err = CacheLockedError(lock)
    assert err.lock_file == lock
    assert str(lock) in str(err)


@pytest.mark.parametrize("error_type", [CacheEmptyError, CacheInterruptedError])
def test_cache_error_without_root_dir(
    error_type: type[CacheEmptyError | CacheInterruptedError],
) -> None:
    """Without ``root_dir_given`` the message suggests a bare ``download()``."""
    err = error_type(ROOT)
    assert err.root == ROOT
    assert err.root_dir_given is False
    assert str(ROOT) in str(err)
    assert "gcatpy.download()" in str(err)


@pytest.mark.parametrize("error_type", [CacheEmptyError, CacheInterruptedError])
def test_cache_error_with_root_dir_shows_pasteable_call(
    error_type: type[CacheEmptyError | CacheInterruptedError],
) -> None:
    """With ``root_dir_given`` the message holds a valid ``root_dir=`` literal."""
    err = error_type(ROOT, root_dir_given=True)
    assert err.root_dir_given is True
    match = _ROOT_DIR_LITERAL.search(str(err))
    assert match is not None
    assert Path(ast.literal_eval(match.group(1))) == ROOT
