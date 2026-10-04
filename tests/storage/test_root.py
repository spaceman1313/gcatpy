"""Tests for locating, creating, and checking the gcatpy data root."""

from dataclasses import FrozenInstanceError
from pathlib import Path

import platformdirs
import pytest

from gcatpy._storage import root as root_module
from gcatpy._storage.root import MARKER_NAME, DataRoot, default_root
from gcatpy.errors import CacheEmptyError, NotAGcatpyRootError, RootNotFoundError

STANDARD_ENTRIES = [MARKER_NAME, "cache", "enumerations", "reports"]
"""What `DataRoot.ensure` creates in an empty root, sorted by name."""


@pytest.fixture(autouse=True)
def default_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Redirect the platform default root into ``tmp_path``; it is not created."""
    path = tmp_path / "default"
    monkeypatch.setattr(root_module, "default_root", lambda: path)
    return path


@pytest.fixture(autouse=True)
def work_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Run each test from an empty current folder inside ``tmp_path``."""
    path = tmp_path / "work"
    path.mkdir()
    monkeypatch.chdir(path)
    return path


def mark(folder: Path) -> Path:
    """Create ``folder`` if needed and put a root marker in it.

    Args:
        folder: The folder to mark.

    Returns:
        The same folder.
    """
    folder.mkdir(parents=True, exist_ok=True)
    (folder / MARKER_NAME).write_text("test marker", encoding="utf-8")
    return folder


def entries(folder: Path) -> list[str]:
    """Return the sorted names in ``folder``.

    Args:
        folder: The folder to list.

    Returns:
        The names of its entries, sorted.
    """
    return sorted(entry.name for entry in folder.iterdir())


# --- DataRoot ---------------------------------------------------------------


@pytest.mark.parametrize(
    ("name", "parts"),
    [
        ("marker", (MARKER_NAME,)),
        ("cache", ("cache",)),
        ("cache_lock", ("cache", ".lock")),
        ("last_attempt", ("cache", "last_attempt.json")),
        ("cache_data", ("cache", "data")),
        ("cache_staging", ("cache", "staging")),
        ("cache_old", ("cache", "data.old")),
        ("metadata", ("cache", "data", "metadata.json")),
        ("enumerations", ("enumerations",)),
        ("reports", ("reports",)),
    ],
)
def test_layout_paths(tmp_path: Path, name: str, parts: tuple[str, ...]) -> None:
    """Each path property points at its place in the root layout."""
    root = DataRoot(tmp_path, "argument")
    assert getattr(root, name) == tmp_path.joinpath(*parts)


def test_relative_path_is_rejected() -> None:
    """Direct construction with a relative path raises ``ValueError``."""
    with pytest.raises(ValueError, match="absolute"):
        DataRoot(Path("relative"), "argument")


def test_data_root_is_frozen(tmp_path: Path) -> None:
    """A resolved root cannot be pointed elsewhere."""
    root = DataRoot(tmp_path, "argument")
    with pytest.raises(FrozenInstanceError):
        root.path = tmp_path / "other"  # pyright: ignore[reportAttributeAccessIssue]


# --- DataRoot.resolve -------------------------------------------------------


def test_resolve_absolute_string(tmp_path: Path) -> None:
    """An absolute string argument is used as given."""
    target = tmp_path / "elsewhere"
    assert DataRoot.resolve(str(target)) == DataRoot(target, "argument")


def test_resolve_path_object(tmp_path: Path) -> None:
    """A ``Path`` argument is accepted like a string."""
    target = tmp_path / "elsewhere"
    assert DataRoot.resolve(target) == DataRoot(target, "argument")


def test_resolve_dot_is_current_folder(work_dir: Path) -> None:
    """``"."`` means the current folder itself, with no subfolder added."""
    assert DataRoot.resolve(".") == DataRoot(work_dir, "argument")


def test_resolve_relative_path(work_dir: Path) -> None:
    """A relative argument is taken relative to the current folder."""
    resolved = DataRoot.resolve("sub/dir")
    assert resolved == DataRoot(work_dir / "sub" / "dir", "argument")


def test_resolve_expands_tilde(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A leading ``~`` becomes the user's home folder."""
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    assert DataRoot.resolve("~/gcat") == DataRoot(home / "gcat", "argument")


def test_resolve_marked_current_folder(work_dir: Path) -> None:
    """With no argument, a current folder holding the marker is the root."""
    mark(work_dir)
    assert DataRoot.resolve() == DataRoot(work_dir, "cwd")


def test_resolve_argument_beats_current_folder(work_dir: Path, tmp_path: Path) -> None:
    """An argument wins even when the current folder is a root."""
    mark(work_dir)
    target = tmp_path / "elsewhere"
    assert DataRoot.resolve(target) == DataRoot(target, "argument")


def test_resolve_ignores_marker_in_parent(
    work_dir: Path, default_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Only the current folder is checked, not its parents."""
    mark(work_dir)
    child = work_dir / "child"
    child.mkdir()
    monkeypatch.chdir(child)
    assert DataRoot.resolve() == DataRoot(default_dir, "default")


def test_resolve_falls_back_to_default(default_dir: Path) -> None:
    """With no argument and no marker, the platform default is the root."""
    assert DataRoot.resolve() == DataRoot(default_dir, "default")


def test_resolve_creates_nothing(work_dir: Path, default_dir: Path) -> None:
    """Resolving never writes to disk."""
    DataRoot.resolve()
    DataRoot.resolve("new-root")
    assert not default_dir.exists()
    assert entries(work_dir) == []


# --- DataRoot.ensure --------------------------------------------------------


def test_ensure_creates_root_with_parents(tmp_path: Path) -> None:
    """A missing root is created with its parents, marker, and folders."""
    root = DataRoot(tmp_path / "a" / "b" / "root", "argument")
    root.ensure()
    assert entries(root.path) == STANDARD_ENTRIES
    assert "gcatpy data root" in root.marker.read_text(encoding="utf-8")


def test_ensure_creates_default_root(default_dir: Path) -> None:
    """The default root is created like any other."""
    root = DataRoot(default_dir, "default")
    root.ensure()
    assert entries(default_dir) == STANDARD_ENTRIES


def test_ensure_is_repeatable_and_keeps_content(tmp_path: Path) -> None:
    """A second call changes nothing and leaves existing files alone."""
    root = DataRoot(tmp_path / "root", "argument")
    root.ensure()
    kept = root.cache / "keep.tsv"
    kept.write_text("data", encoding="utf-8")
    marker_text = root.marker.read_text(encoding="utf-8")

    root.ensure()

    assert kept.read_text(encoding="utf-8") == "data"
    assert root.marker.read_text(encoding="utf-8") == marker_text


def test_ensure_adopts_empty_folder(tmp_path: Path) -> None:
    """An existing empty folder becomes a root."""
    folder = tmp_path / "empty"
    folder.mkdir()
    DataRoot(folder, "argument").ensure()
    assert entries(folder) == STANDARD_ENTRIES


def test_ensure_accepts_marked_folder_with_content(tmp_path: Path) -> None:
    """A folder that already has the marker may hold other files."""
    folder = mark(tmp_path / "marked")
    (folder / "notes.txt").write_text("mine", encoding="utf-8")
    DataRoot(folder, "argument").ensure()
    assert entries(folder) == sorted([*STANDARD_ENTRIES, "notes.txt"])


def test_ensure_refuses_unmarked_folder_with_content(tmp_path: Path) -> None:
    """A non-empty folder without the marker is refused and left untouched."""
    folder = tmp_path / "theirs"
    folder.mkdir()
    (folder / "notes.txt").write_text("mine", encoding="utf-8")
    with pytest.raises(NotAGcatpyRootError) as excinfo:
        DataRoot(folder, "argument").ensure()
    assert excinfo.value.is_file is False
    assert entries(folder) == ["notes.txt"]


def test_ensure_refuses_file(tmp_path: Path) -> None:
    """A path naming a file is refused."""
    file = tmp_path / "afile"
    file.write_text("x", encoding="utf-8")
    with pytest.raises(NotAGcatpyRootError) as excinfo:
        DataRoot(file, "argument").ensure()
    assert excinfo.value.is_file is True
    assert file.is_file()


# --- DataRoot.require_existing ----------------------------------------------


def test_require_existing_passes_on_created_root(tmp_path: Path) -> None:
    """A root made by ``ensure`` passes the check."""
    root = DataRoot(tmp_path / "root", "argument")
    root.ensure()
    root.require_existing()


def test_require_existing_missing_default_is_empty_cache(default_dir: Path) -> None:
    """A missing default root reads as "nothing downloaded yet"."""
    with pytest.raises(CacheEmptyError) as excinfo:
        DataRoot(default_dir, "default").require_existing()
    assert excinfo.value.root == default_dir
    assert not default_dir.exists()


def test_require_existing_missing_argument_root(tmp_path: Path) -> None:
    """A missing root the user named raises ``RootNotFoundError``."""
    missing = tmp_path / "typo"
    with pytest.raises(RootNotFoundError) as excinfo:
        DataRoot(missing, "argument").require_existing()
    assert excinfo.value.path == missing
    assert not missing.exists()


def test_require_existing_unmarked_folder(tmp_path: Path) -> None:
    """An existing folder without the marker is not a root."""
    folder = tmp_path / "plain"
    folder.mkdir()
    with pytest.raises(NotAGcatpyRootError) as excinfo:
        DataRoot(folder, "argument").require_existing()
    assert excinfo.value.is_file is False
    assert entries(folder) == []


def test_require_existing_file(tmp_path: Path) -> None:
    """A path naming a file is refused with ``is_file=True``."""
    file = tmp_path / "afile"
    file.write_text("x", encoding="utf-8")
    with pytest.raises(NotAGcatpyRootError) as excinfo:
        DataRoot(file, "argument").require_existing()
    assert excinfo.value.is_file is True


# --- DataRoot.require_marker ------------------------------------------------


def test_require_marker_passes_with_marker(tmp_path: Path) -> None:
    """A marked folder passes."""
    DataRoot(mark(tmp_path / "marked"), "argument").require_marker()


def test_require_marker_raises_without_marker(tmp_path: Path) -> None:
    """An unmarked folder is refused."""
    folder = tmp_path / "plain"
    folder.mkdir()
    with pytest.raises(NotAGcatpyRootError):
        DataRoot(folder, "argument").require_marker()


# --- default_root -----------------------------------------------------------


def test_default_root_is_platform_data_dir() -> None:
    """The unpatched default is the platformdirs per-user data folder."""
    expected = Path(platformdirs.user_data_dir("gcatpy", appauthor=False))
    assert default_root() == expected
