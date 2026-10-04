"""Public exceptions raised by gcatpy.

Every exception derives from `GcatpyError`, so callers can catch all gcatpy
errors with one clause. Each exception builds its own message from its
arguments and keeps them as attributes for programmatic use.
"""

from pathlib import Path

__all__ = [
    "CacheEmptyError",
    "CacheInterruptedError",
    "CacheLockedError",
    "GcatpyError",
    "NotAGcatpyRootError",
    "RootNotFoundError",
]


class GcatpyError(Exception):
    """Base class for every error gcatpy raises."""


class RootNotFoundError(GcatpyError):
    """The data root folder does not exist.

    Attributes:
        path: The root folder that does not exist.
    """

    path: Path

    def __init__(self, path: Path) -> None:
        """Initialize the error.

        Args:
            path: The root folder that does not exist.
        """
        self.path = path
        super().__init__(
            f"The data root {path} does not exist. Check the path; if it is a new "
            "root, gcatpy.download(root_dir=...) creates it."
        )


class NotAGcatpyRootError(GcatpyError):
    """gcatpy refused to use a path as a data root.

    gcatpy only reads from, or writes to, folders it created itself, which it
    identifies by the ``.gcatpy-root`` marker file. ``download`` may also adopt
    an empty folder. A path that names a file is never a root.

    Attributes:
        path: The path that was refused.
        is_file: Whether ``path`` is a file rather than a folder without the
            marker.
    """

    path: Path
    is_file: bool

    def __init__(self, path: Path, *, is_file: bool = False) -> None:
        """Initialize the error.

        Args:
            path: The path that was refused.
            is_file: Whether ``path`` is a file rather than a folder.
        """
        self.path = path
        self.is_file = is_file
        if is_file:
            message = (
                f"{path} is a file, not a folder, so it cannot be a gcatpy data root."
            )
        else:
            message = (
                f"{path} is not a gcatpy data root: it has no .gcatpy-root marker "
                "file. A data root must be a folder gcatpy created, or an empty "
                "folder for download() to use."
            )
        super().__init__(message)


class CacheLockedError(GcatpyError):
    """Another download holds the cache lock.

    Attributes:
        lock_file: The lock file that is already held.
    """

    lock_file: Path

    def __init__(self, lock_file: Path) -> None:
        """Initialize the error.

        Args:
            lock_file: The lock file that is already held.
        """
        self.lock_file = lock_file
        super().__init__(
            f"Another gcatpy download is using this cache (lock file {lock_file}). "
            "If no download is running, an earlier one was interrupted: delete "
            "the lock file and try again."
        )


class CacheEmptyError(GcatpyError):
    """The cache holds no downloaded GCAT data.

    Attributes:
        root: The data root whose cache is empty.
        root_dir_given: Whether the root came from a ``root_dir=`` argument, in
            which case the message shows the exact ``download`` call to run.
    """

    root: Path
    root_dir_given: bool

    def __init__(self, root: Path, *, root_dir_given: bool = False) -> None:
        """Initialize the error.

        Args:
            root: The data root whose cache is empty.
            root_dir_given: Whether the root came from a ``root_dir=`` argument.
        """
        self.root = root
        self.root_dir_given = root_dir_given
        call = f"download(root_dir={str(root)!r})" if root_dir_given else "download()"
        super().__init__(
            f"No GCAT data has been downloaded into {root} yet. "
            f"Call gcatpy.{call} to fetch it."
        )


class CacheInterruptedError(GcatpyError):
    """The cache is mid-swap: ``cache/data/`` is missing, ``cache/data.old/`` is not.

    A download was interrupted while replacing the cache, or is still running.
    Only ``download`` repairs this; reading functions raise this error instead.

    Attributes:
        root: The data root whose cache is mid-swap.
        root_dir_given: Whether the root came from a ``root_dir=`` argument, in
            which case the message shows the exact ``download`` call to run.
    """

    root: Path
    root_dir_given: bool

    def __init__(self, root: Path, *, root_dir_given: bool = False) -> None:
        """Initialize the error.

        Args:
            root: The data root whose cache is mid-swap.
            root_dir_given: Whether the root came from a ``root_dir=`` argument.
        """
        self.root = root
        self.root_dir_given = root_dir_given
        call = f"download(root_dir={str(root)!r})" if root_dir_given else "download()"
        super().__init__(
            f"A download into {root} was interrupted or is still running "
            "(cache/data/ is missing, cache/data.old/ is present). "
            f"Call gcatpy.{call} again to repair the cache."
        )
