import os
import shutil
import stat
import sys
import time
from collections.abc import Callable
from pathlib import Path
from types import TracebackType
from typing import Any

# Windows refuses to unlink a file whose read-only attribute is set, and refuses to unlink a
# file another process still holds open. Neither blocks a delete on POSIX, where only the
# parent directory's write bit matters. A read-only file is fixed by clearing the attribute; an
# open handle is usually a scanner or indexer that lets go within a moment, so retry briefly.
_RETRY_COUNT = 5
_RETRY_INTERVAL = 0.1


def _clear_read_only_and_retry(func: Callable[[str], Any], path: str, exc: BaseException) -> None:
    # rmtree reports failures from every stage of the walk here, not just deletions: scandir,
    # open, lstat, close, rmdir and unlink all route through this hook, and a failure raised
    # from the hook is caught again by rmtree's outer handler and reported a second time with
    # func set to the stage that was in progress. Only the removal calls may be retried --
    # re-running something like scandir would succeed and make a failure nothing fixed look
    # handled, silently resuming a delete that should have stopped. Resolve the names on each
    # call so a test that patches them still matches.
    if not isinstance(exc, PermissionError) or func not in (os.unlink, os.rmdir):
        raise exc

    try:
        os.chmod(path, stat.S_IWRITE)
    except OSError:
        raise exc from None

    for attempt in range(_RETRY_COUNT):
        try:
            func(path)
            return
        except PermissionError as retry_exc:
            if attempt == _RETRY_COUNT - 1:
                raise retry_exc
            time.sleep(_RETRY_INTERVAL * (attempt + 1))


def _on_error(
    func: Callable[[str], Any],
    path: str,
    exc_info: tuple[type[BaseException], BaseException, TracebackType | None],
) -> None:
    """Adapter for the pre-3.12 ``onerror`` signature, which passes an exc_info triple."""
    _clear_read_only_and_retry(func, path, exc_info[1])


def rmtree(path: Path | str) -> None:
    """``shutil.rmtree`` that tolerates the two ways a delete fails on Windows but not POSIX.

    Clears the read-only attribute (git writes object and pack files as mode 0444) and retries
    briefly when another process still holds the file open. Errors that survive the retries are
    raised, never swallowed.
    """
    if sys.version_info >= (3, 12):
        shutil.rmtree(path, onexc=_clear_read_only_and_retry)
    else:
        shutil.rmtree(path, onerror=_on_error)
