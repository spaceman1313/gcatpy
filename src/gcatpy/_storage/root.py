"""Locate the gcatpy data root and describe its layout.

The data root is the one folder that holds everything gcatpy stores on the
user's machine::

    <data root>/
        .gcatpy-root    marker identifying a folder gcatpy created
        cache/          downloaded GCAT files
        enumerations/   code tables the user may edit
        reports/        load and download reports

Every public function that uses a root picks it the same way; the first rule
that applies wins:

1. A ``root_dir=`` argument. That folder itself is the root. A leading ``~``
   means the user's home folder; any other relative path, including ``"."``,
   is taken relative to the current folder.
2. The current folder, if it holds the ``.gcatpy-root`` marker. Parent folders
   are not searched.
3. The platform default, ``platformdirs.user_data_dir("gcatpy",
   appauthor=False)``, for example ``~/.local/share/gcatpy`` on Linux.

Only ``download`` creates a root, through `DataRoot.ensure`. Every other
function calls `DataRoot.require_existing` and changes nothing on disk.
Nothing is read at import time.
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Literal, Self

import platformdirs

from gcatpy.errors import CacheEmptyError, NotAGcatpyRootError, RootNotFoundError

MARKER_NAME: Final = ".gcatpy-root"
"""File that identifies a folder as a gcatpy-created data root."""

_MARKER_TEXT: Final = (
    "This folder is a gcatpy data root. gcatpy only deletes or replaces files\n"
    "inside folders that contain this marker. Do not copy it into other folders.\n"
)

type RootSource = Literal["argument", "cwd", "default"]
"""Which rule chose a resolved root: argument, current folder, or default."""


def default_root() -> Path:
    """Return the platform default data root.

    Returns:
        ``platformdirs.user_data_dir("gcatpy", appauthor=False)``. The folder is
        not created.
    """
    return Path(platformdirs.user_data_dir("gcatpy", appauthor=False))


@dataclass(frozen=True, slots=True)
class DataRoot:
    """A resolved data root and the path of every file and folder inside it.

    Constructing a `DataRoot` and reading its path properties performs no I/O;
    the folders may not exist yet. `resolve` reads at most one marker file,
    `ensure` creates folders, and the ``require_*`` methods only read.

    Attributes:
        path: Absolute path of the root folder.
        source: Which rule chose the root.
    """

    path: Path
    source: RootSource

    def __post_init__(self) -> None:
        """Reject a relative path, which direct construction does not resolve.

        Raises:
            ValueError: If ``path`` is not absolute.
        """
        if not self.path.is_absolute():
            raise ValueError(f"DataRoot path must be absolute, got {self.path}")

    @classmethod
    def resolve(cls, root_dir: str | os.PathLike[str] | None = None) -> Self:
        """Pick the data root without changing anything on disk.

        Uses ``root_dir`` if given, else the current folder if it holds the
        marker, else the platform default. The chosen folder is not checked for
        existence; see `ensure` and `require_existing`.

        Args:
            root_dir: A folder the user passed explicitly, or ``None``.

        Returns:
            The resolved root, with an absolute path. A leading ``~`` in
            ``root_dir`` is expanded to the user's home folder.
        """
        if root_dir is not None:
            return cls(Path(root_dir).expanduser().absolute(), "argument")
        cwd = Path.cwd()
        if (cwd / MARKER_NAME).is_file():
            return cls(cwd, "cwd")
        return cls(default_root(), "default")

    @property
    def marker(self) -> Path:
        """The ``.gcatpy-root`` marker file."""
        return self.path / MARKER_NAME

    @property
    def cache(self) -> Path:
        """The ``cache/`` folder."""
        return self.path / "cache"

    @property
    def cache_lock(self) -> Path:
        """The ``cache/.lock`` file held during a download."""
        return self.cache / ".lock"

    @property
    def last_attempt(self) -> Path:
        """The ``cache/last_attempt.json`` download outcome file."""
        return self.cache / "last_attempt.json"

    @property
    def cache_data(self) -> Path:
        """The live cache folder, ``cache/data/``."""
        return self.cache / "data"

    @property
    def cache_staging(self) -> Path:
        """The ``cache/staging/`` folder used during a download."""
        return self.cache / "staging"

    @property
    def cache_old(self) -> Path:
        """The ``cache/data.old/`` folder used during the final swap."""
        return self.cache / "data.old"

    @property
    def metadata(self) -> Path:
        """The live cache's ``cache/data/metadata.json``."""
        return self.cache_data / "metadata.json"

    @property
    def enumerations(self) -> Path:
        """The ``enumerations/`` folder of user-editable code tables."""
        return self.path / "enumerations"

    @property
    def reports(self) -> Path:
        """The ``reports/`` folder of load and download reports."""
        return self.path / "reports"

    def ensure(self) -> None:
        """Create the root, its marker, and its standard folders, if missing.

        Used only by ``download``. The root folder is created with any missing
        parents. An existing folder is adopted as a root only if it already has
        the marker or is empty. Then the marker and the ``cache/``,
        ``enumerations/``, and ``reports/`` folders are created if missing.
        Safe to call repeatedly.

        Raises:
            NotAGcatpyRootError: If the path is a file, or the folder exists,
                has content, and lacks the marker.
        """
        self._reject_file()
        self.path.mkdir(parents=True, exist_ok=True)

        if not self.marker.is_file():
            if any(self.path.iterdir()):
                raise NotAGcatpyRootError(self.path)
            self.marker.write_text(_MARKER_TEXT, encoding="utf-8")

        for folder in (self.cache, self.enumerations, self.reports):
            folder.mkdir(exist_ok=True)

    def require_existing(self) -> None:
        """Check that the root exists, for every function except ``download``.

        Creates nothing. A missing default root means nothing has been
        downloaded yet, so it is reported as an empty cache rather than a
        missing folder the user never chose.

        Raises:
            CacheEmptyError: If the root is the platform default and does not
                exist.
            RootNotFoundError: If any other root does not exist.
            NotAGcatpyRootError: If the path is a file, or the folder exists but
                has no marker.
        """
        self._reject_file()
        if not self.path.is_dir():
            if self.source == "default":
                raise CacheEmptyError(self.path)
            raise RootNotFoundError(self.path)
        self.require_marker()

    def require_marker(self) -> None:
        """Check that the root carries the marker before anything is deleted in it.

        Raises:
            NotAGcatpyRootError: If the root has no ``.gcatpy-root`` marker file.
        """
        if not self.marker.is_file():
            raise NotAGcatpyRootError(self.path)

    def _reject_file(self) -> None:
        """Refuse a root path that names an existing file.

        Raises:
            NotAGcatpyRootError: If the root path exists and is not a folder.
        """
        if self.path.exists() and not self.path.is_dir():
            raise NotAGcatpyRootError(self.path, is_file=True)
