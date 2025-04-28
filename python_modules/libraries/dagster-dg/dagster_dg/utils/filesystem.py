import datetime
import hashlib
import time
from collections.abc import Sequence
from pathlib import Path
from typing import Any, Callable, Optional

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from dagster_dg.utils import (
    DEFAULT_FILE_EXCLUDE_PATTERNS,
    clear_screen,
    hash_directory_metadata,
    hash_file_metadata,
)


def hash_paths(
    paths: Sequence[Path],
    includes: Optional[Sequence[str]] = None,
    excludes: Sequence[str] = DEFAULT_FILE_EXCLUDE_PATTERNS,
    error_on_missing: bool = True,
) -> str:
    """Hash the given paths, including their metadata.

    Args:
        paths: The paths to hash.
        includes: A list of glob patterns to target, excluding files that don't match any of the patterns.
        excludes: A list of glob patterns to exclude, including files that match any of the patterns. Defaults to
            various Python-related files that are not relevant to the contents of the project.

    Returns:
        The hash of the paths.
    """
    hasher = hashlib.md5()
    for path in paths:
        if path.is_dir():
            hash_directory_metadata(
                hasher,
                path,
                includes=includes,
                excludes=excludes,
                error_on_missing=error_on_missing,
            )
        else:
            hash_file_metadata(hasher, path, error_on_missing=error_on_missing)
    return hasher.hexdigest()


class PathChangeHandler(FileSystemEventHandler):
    """Basic handler that clears the screen and re-executes the callback when any of the watched paths change
    in a way that would affect the hash of the paths. Passes the new hash to the callback.
    """

    def __init__(
        self,
        paths: Sequence[Path],
        includes: Optional[Sequence[str]],
        excludes: Sequence[str],
        callback: Callable[[str], Any],
    ):
        self._callback = callback
        self._paths = paths
        self._includes = includes
        self._excludes = excludes
        self._prev_hash = hash_paths(self._paths, self._includes, self._excludes)
        self.clear_and_execute(self._prev_hash)

    def dispatch(self, _event: FileSystemEvent):  # pyright: ignore[reportIncompatibleMethodOverride]
        new_hash = hash_paths(self._paths, self._includes, self._excludes, error_on_missing=False)

        if new_hash != self._prev_hash:
            self.clear_and_execute(new_hash)
            self._prev_hash = new_hash

    def clear_and_execute(self, new_hash: str):
        clear_screen()
        self._callback(new_hash)
        current_time = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"\nUpdated at {current_time}, watching for changes...")  # noqa: T201


# This is a global variable that is used to signal the watcher to exit in tests
SHOULD_WATCHER_EXIT = False


def watch_paths(
    paths: Sequence[Path],
    callback: Callable[[str], Any],
    includes: Optional[Sequence[str]] = None,
    excludes: Sequence[str] = DEFAULT_FILE_EXCLUDE_PATTERNS,
):
    """Watches the given paths for changes and calls the callback when they change.
    The callback should take a single argument, the new hash of the paths.

    Runs synchronously until the observer is stopped, or keyboard interrupt is received.

    Args:
        paths: The paths to watch.
        callback: The callback to call when path contents change.
        includes: A list of glob patterns to target, excluding files that don't match any of the patterns.
        excludes: A list of glob patterns to exclude, including files that match any of the patterns. Defaults to
            various Python-related files that are not relevant to the contents of the project.
    """
    observer = Observer()
    handler = PathChangeHandler(paths, includes, excludes, callback)
    for path in paths:
        observer.schedule(handler, str(path), recursive=True)
    observer.start()
    try:
        while observer.is_alive() and not SHOULD_WATCHER_EXIT:
            time.sleep(0.5)
    finally:
        observer.stop()
        observer.join()
