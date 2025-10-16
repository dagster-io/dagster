import os
from abc import ABC, abstractmethod
from collections.abc import Generator, Iterator, Sequence
from contextlib import contextmanager
from enum import Enum
from typing import IO, Callable, Final, NamedTuple, Optional

from typing_extensions import Self

import dagster._check as check
from dagster._annotations import public
from dagster._core.captured_log_api import LogLineCursor
from dagster._core.instance import MayHaveInstanceWeakref, T_DagsterInstance
from dagster._record import record
from dagster._serdes import whitelist_for_serdes

MAX_BYTES_CHUNK_READ: Final = 1048576  # 1 MB


class ComputeIOType(Enum):
    STDOUT = "stdout"
    STDERR = "stderr"


@whitelist_for_serdes
@record
class LogRetrievalShellCommand:
    stdout: Optional[str]
    stderr: Optional[str]


class CapturedLogContext(
    NamedTuple(
        "_CapturedLogContext",
        [
            ("log_key", Sequence[str]),
            ("external_url", Optional[str]),
            ("external_stdout_url", Optional[str]),
            ("external_stderr_url", Optional[str]),
            ("shell_cmd", Optional[LogRetrievalShellCommand]),
        ],
    )
):
    """Object representing the context in which logs are captured.  Can be used by external logging
    sidecar implementations to point the Dagster UI to an external url to view compute logs instead of a
    Dagster-managed location.
    """

    def __new__(
        cls,
        log_key: Sequence[str],
        external_stdout_url: Optional[str] = None,
        external_stderr_url: Optional[str] = None,
        external_url: Optional[str] = None,
        shell_cmd: Optional[LogRetrievalShellCommand] = None,
    ):
        if external_url and (external_stdout_url or external_stderr_url):
            check.failed(
                "Cannot specify both `external_url` and one of"
                " `external_stdout_url`/`external_stderr_url`"
            )

        return super().__new__(
            cls,
            log_key,
            external_stdout_url=external_stdout_url,
            external_stderr_url=external_stderr_url,
            external_url=external_url,
            shell_cmd=shell_cmd,
        )


class CapturedLogData(
    NamedTuple(
        "_CapturedLogData",
        [
            ("log_key", Sequence[str]),
            ("stdout", Optional[bytes]),
            ("stderr", Optional[bytes]),
            ("cursor", Optional[str]),
        ],
    )
):
    """Object representing captured log data, either a partial chunk of the log data or the full
    capture.  Contains the raw bytes and optionally the cursor offset for the partial chunk.
    """

    def __new__(
        cls,
        log_key: Sequence[str],
        stdout: Optional[bytes] = None,
        stderr: Optional[bytes] = None,
        cursor: Optional[str] = None,
    ):
        return super().__new__(cls, log_key, stdout, stderr, cursor)


class CapturedLogMetadata(
    NamedTuple(
        "_CapturedLogMetadata",
        [
            ("stdout_location", Optional[str]),
            ("stderr_location", Optional[str]),
            ("stdout_download_url", Optional[str]),
            ("stderr_download_url", Optional[str]),
        ],
    )
):
    """Object representing metadata info for the captured log data.
    It can contain:
     - a display string for the location of the log data,
     - a URL for direct download of the captured log data.
    """

    def __new__(
        cls,
        stdout_location: Optional[str] = None,
        stderr_location: Optional[str] = None,
        stdout_download_url: Optional[str] = None,
        stderr_download_url: Optional[str] = None,
    ):
        return super().__new__(
            cls,
            stdout_location=stdout_location,
            stderr_location=stderr_location,
            stdout_download_url=stdout_download_url,
            stderr_download_url=stderr_download_url,
        )


class CapturedLogSubscription:
    def __init__(
        self,
        manager: "ComputeLogManager[T_DagsterInstance]",
        log_key: Sequence[str],
        cursor: Optional[str],
    ):
        self._manager = manager
        self._log_key = log_key
        self._cursor = cursor
        self._observer: Optional[Callable[[CapturedLogData], None]] = None
        self.is_complete = False

    def __call__(self, observer: Optional[Callable[[CapturedLogData], None]]) -> Self:
        self._observer = observer
        self.fetch()
        if self._manager.is_capture_complete(self._log_key):
            self.complete()
        return self

    @property
    def log_key(self) -> Sequence[str]:
        return self._log_key

    def dispose(self) -> None:
        self._observer = None
        self._manager.unsubscribe(self)

    def fetch(self) -> None:
        if not self._observer:
            return

        should_fetch = True
        while should_fetch:
            log_data = self._manager.get_log_data(
                self._log_key,
                self._cursor,
                max_bytes=MAX_BYTES_CHUNK_READ,
            )
            if not self._cursor or log_data.cursor != self._cursor:
                self._observer(log_data)
                self._cursor = log_data.cursor
            should_fetch = _has_max_data(log_data.stdout) or _has_max_data(log_data.stderr)

    def complete(self) -> None:
        self.is_complete = True


def _has_max_data(chunk: Optional[bytes]) -> bool:
    # function is used as predicate but does not actually return a boolean
    return chunk and len(chunk) >= MAX_BYTES_CHUNK_READ  # type: ignore


@public
class ComputeLogManager(ABC, MayHaveInstanceWeakref[T_DagsterInstance]):
    """Abstract base class for capturing the unstructured logs (stdout/stderr) in the current
    process, stored / retrieved with a provided log_key.
    """

    @abstractmethod
    @contextmanager
    def capture_logs(self, log_key: Sequence[str]) -> Generator[CapturedLogContext, None, None]:
        """Context manager for capturing the stdout/stderr within the current process, and persisting
        it under the given log key.

        Args:
            log_key (List[String]): The log key identifying the captured logs
        """

    @abstractmethod
    @contextmanager
    def open_log_stream(
        self, log_key: Sequence[str], io_type: ComputeIOType
    ) -> Iterator[Optional[IO[bytes]]]:
        """Context manager for providing an IO stream that enables the caller to write to a log stream
        managed by the captured log manager, to be read later using the given log key.

        Args:
            log_key (List[String]): The log key identifying the captured logs
        """

    @abstractmethod
    def is_capture_complete(self, log_key: Sequence[str]) -> bool:
        """Flag indicating when the log capture for a given log key has completed.

        Args:
            log_key (List[String]): The log key identifying the captured logs

        Returns:
            Boolean
        """

    @abstractmethod
    def get_log_data_for_type(
        self,
        log_key: Sequence[str],
        io_type: ComputeIOType,
        offset: int,
        max_bytes: Optional[int],
    ) -> tuple[Optional[bytes], int]:
        """Returns a chunk of the captured io_type logs for a given log key.

        Args:
            log_key (List[String]): The log key identifying the captured logs
            io_type (ComputeIOType): stderr or stdout
            offset (Optional[int]): An offset in to the log to start from
            max_bytes (Optional[int]): A limit on the size of the log chunk to fetch

        Returns:
            Tuple[Optional[bytes], int]: The content read and offset in to the file
        """

    @abstractmethod
    def get_log_metadata(self, log_key: Sequence[str]) -> CapturedLogMetadata:
        """Returns the metadata of the captured logs for a given log key, including
        displayable information on where the logs are persisted.

        Args:
            log_key (List[String]): The log key identifying the captured logs

        Returns:
            CapturedLogMetadata
        """

    @abstractmethod
    def delete_logs(
        self,
        log_key: Optional[Sequence[str]] = None,
        prefix: Optional[Sequence[str]] = None,
    ) -> None:
        """Deletes the captured logs for a given log key.

        Args:
            log_key(Optional[List[String]]): The log key of the logs to delete
            prefix(Optional[List[String]]): The prefix of the log keys to delete
        """

    @abstractmethod
    def subscribe(
        self, log_key: Sequence[str], cursor: Optional[str] = None
    ) -> CapturedLogSubscription:
        """Registers an observable object for log data.

        Args:
            log_key (List[String]): The log key identifying the captured logs
            cursor (Optional[String]): The string cursor marking the position within the log stream
        Returns:
            CapturedLogSubscription
        """

    def unsubscribe(self, subscription: CapturedLogSubscription) -> None:
        """Deregisters an observable object from receiving log updates.

        Args:
            subscription (CapturedLogSubscription): subscription object which manages when to send
                back data to the subscriber
        """
        pass

    def dispose(self):
        pass

    def parse_cursor(self, cursor: Optional[str] = None) -> tuple[int, int]:
        # Translates a string cursor into a set of byte offsets for stdout, stderr
        if not cursor:
            return 0, 0

        parts = cursor.split(":")
        if not parts or len(parts) != 2:
            return 0, 0

        stdout, stderr = [int(_) for _ in parts]
        return stdout, stderr

    def build_cursor(self, stdout_offset: int, stderr_offset: int) -> str:
        return f"{stdout_offset}:{stderr_offset}"

    def get_log_data(
        self,
        log_key: Sequence[str],
        cursor: Optional[str] = None,
        max_bytes: Optional[int] = None,
    ) -> CapturedLogData:
        stdout_offset, stderr_offset = self.parse_cursor(cursor)
        stdout, new_stdout_offset = self.get_log_data_for_type(
            log_key,
            ComputeIOType.STDOUT,
            stdout_offset,
            max_bytes,
        )
        stderr, new_stderr_offset = self.get_log_data_for_type(
            log_key,
            ComputeIOType.STDERR,
            stderr_offset,
            max_bytes,
        )
        return CapturedLogData(
            log_key=log_key,
            stdout=stdout,
            stderr=stderr,
            cursor=self.build_cursor(new_stdout_offset, new_stderr_offset),
        )

    def build_log_key_for_run(self, run_id: str, step_key: str) -> Sequence[str]:
        """Legacy adapter to translate run_id/key to captured log manager-based log_key."""
        return [run_id, "compute_logs", step_key]

    def get_log_keys_for_log_key_prefix(
        self, log_key_prefix: Sequence[str], io_type: ComputeIOType
    ) -> Sequence[Sequence[str]]:
        """Returns the logs keys for a given log key prefix. This is determined by looking at the
        directory defined by the log key prefix and creating a log_key for each file in the directory.
        """
        raise NotImplementedError("Must implement get_log_keys_for_log_key_prefix")

    def _get_log_lines_for_log_key(
        self,
        log_key: Sequence[str],
        io_type: ComputeIOType,
    ) -> Sequence[str]:
        """For a log key, gets the corresponding file, and splits the file into lines."""
        log_data, _ = self.get_log_data_for_type(
            log_key,
            io_type,
            offset=0,
            max_bytes=None,
        )
        raw_logs = log_data.decode("utf-8") if log_data else ""
        log_lines = raw_logs.split("\n")

        return log_lines

    def read_log_lines_for_log_key_prefix(
        self,
        log_key_prefix: Sequence[str],
        cursor: Optional[str],
        io_type: ComputeIOType,
    ) -> tuple[Sequence[str], Optional[LogLineCursor]]:
        """For a given directory defined by log_key_prefix that contains files, read the logs from the files
        as if they are a single continuous file. Reads env var DAGSTER_CAPTURED_LOG_CHUNK_SIZE lines at a time.
        Returns the lines read and the next cursor.

        Note that the has_more_now attribute of the cursor indicates if there are more logs that can be read immediately.
        If has_more_now if False, the process producing logs could still be running and dump more logs into the
        directory at a later time.
        """
        num_lines = int(os.getenv("DAGSTER_CAPTURED_LOG_CHUNK_SIZE", "1000"))
        # find all of the log_keys to read from and sort them in the order to be read
        log_keys = sorted(
            self.get_log_keys_for_log_key_prefix(log_key_prefix, io_type=io_type),
            key=lambda x: "/".join(x),
        )
        if len(log_keys) == 0:
            return [], None

        log_cursor = LogLineCursor.parse(cursor) if cursor else None
        if log_cursor is None:
            log_key_to_fetch_idx = 0
            line_cursor = 0
        else:
            log_key_to_fetch_idx = log_keys.index(log_cursor.log_key)
            line_cursor = log_cursor.line

        if line_cursor == -1:
            # line_cursor for -1 means the entirety of the file has been read, but the next file
            # didn't exist yet. So we see if a new file has been added.
            # if the next file doesn't exist yet, return
            if log_key_to_fetch_idx + 1 >= len(log_keys):
                return [], log_cursor
            log_key_to_fetch_idx += 1
            line_cursor = 0

        log_lines = self._get_log_lines_for_log_key(log_keys[log_key_to_fetch_idx], io_type=io_type)
        records = []
        has_more = True

        while len(records) < num_lines:
            remaining_log_lines = log_lines[line_cursor:]
            remaining_lines_to_fetch = num_lines - len(records)
            if remaining_lines_to_fetch < len(remaining_log_lines):
                records.extend(remaining_log_lines[:remaining_lines_to_fetch])
                line_cursor += remaining_lines_to_fetch
            else:
                records.extend(remaining_log_lines)
                line_cursor = -1

            if line_cursor == -1:
                # we've read the entirety of the file, update the cursor
                if log_key_to_fetch_idx + 1 >= len(log_keys):
                    # no more files to process
                    has_more = False
                    break
                log_key_to_fetch_idx += 1
                line_cursor = 0
                if len(records) < num_lines:
                    # we still need more records, so fetch the next file
                    log_lines = self._get_log_lines_for_log_key(
                        log_keys[log_key_to_fetch_idx], io_type=io_type
                    )

        new_cursor = LogLineCursor(
            log_key=log_keys[log_key_to_fetch_idx],
            line=line_cursor,
            has_more_now=has_more,
        )
        return records, new_cursor
