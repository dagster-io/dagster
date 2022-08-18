# pylint: disable=unused-argument

from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import List, NamedTuple, Optional

MAX_BYTES_CHUNK_READ = 4194304  # 4 MB


class CapturedLogData(
    NamedTuple(
        "_CapturedLogData",
        [
            ("log_key", List[str]),
            ("stdout", Optional[bytes]),
            ("stderr", Optional[bytes]),
            ("cursor", Optional[str]),
        ],
    )
):
    """
    Object representing captured log data, either a partial chunk of the log data or the full
    capture.  Contains the raw bytes and optionally the cursor offset for the partial chunk.
    """

    def __new__(
        cls,
        log_key: List[str],
        stdout: Optional[bytes] = None,
        stderr: Optional[bytes] = None,
        cursor: Optional[str] = None,
    ):
        return super(CapturedLogData, cls).__new__(cls, log_key, stdout, stderr, cursor)


class CapturedLogMetadata(
    NamedTuple(
        "_CapturedLogMetadata",
        [
            ("external_url", Optional[str]),
            ("stdout_location", Optional[str]),
            ("stderr_location", Optional[str]),
            ("stdout_download_url", Optional[str]),
            ("stderr_download_url", Optional[str]),
        ],
    )
):
    """
    Object representing metadata info for the captured log data, containing a display string for
    the location of the log data and a URL for direct download of the captured log data.
    """

    def __new__(
        cls,
        external_url: Optional[str] = None,
        stdout_location: Optional[str] = None,
        stderr_location: Optional[str] = None,
        stdout_download_url: Optional[str] = None,
        stderr_download_url: Optional[str] = None,
    ):
        return super(CapturedLogMetadata, cls).__new__(
            cls,
            external_url=external_url,
            stdout_location=stdout_location,
            stderr_location=stderr_location,
            stdout_download_url=stdout_download_url,
            stderr_download_url=stderr_download_url,
        )


class CapturedLogSubscription:
    def __init__(self, manager, log_key, cursor):
        self._manager = manager
        self._log_key = log_key
        self._cursor = cursor
        self._observer = None

    def __call__(self, observer):
        self._observer = observer
        self.fetch()
        if self._manager.is_capture_complete(self._log_key):
            self.complete()
        return self

    @property
    def log_key(self):
        return self._log_key

    def dispose(self):
        # called when the connection gets closed, allowing the observer to get GC'ed
        if self._observer and callable(getattr(self._observer, "dispose", None)):
            self._observer.dispose()
        self._observer = None
        self._manager.on_unsubscribe(self)

    def fetch(self):
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
                self._observer.on_next(log_data)
                self._cursor = log_data.cursor
            should_fetch = _has_max_data(log_data.stdout) or _has_max_data(log_data.stderr)

    def complete(self):
        if not self._observer:
            return
        self._observer.on_completed()


def _has_max_data(chunk):
    return chunk and len(chunk) >= MAX_BYTES_CHUNK_READ


class CapturedLogManager(ABC):
    """Abstract base class for capturing the unstructured logs (stdout/stderr) in the current
    process, stored / retrieved with a provided log_key."""

    @abstractmethod
    @contextmanager
    def capture_logs(self, log_key: List[str]):
        """
        Context manager for capturing the stdout/stderr within the current process, and persisting
        it under the given log key.

        Args:
            log_key (List[String]): The log key identifying the captured logs
        """

    @abstractmethod
    def is_capture_complete(self, log_key: List[str]):
        """Flag indicating when the log capture for a given log key has completed.

        Args:
            log_key (List[String]): The log key identifying the captured logs

        Returns:
            Boolean
        """

    @abstractmethod
    def on_progress(self, log_key: List[str]):
        """Utility method that can be called periodically while logs are being captured, in order
        to support different batched streaming implementations.

        Args:
            log_key (List[String]): The log key identifying the captured logs

        """

    @abstractmethod
    def get_log_data(
        self,
        log_key: List[str],
        cursor: Optional[str] = None,
        max_bytes: Optional[int] = None,
    ) -> CapturedLogData:
        """Returns a chunk of the captured stdout logs for a given log key

        Args:
            log_key (List[String]): The log key identifying the captured logs
            cursor (Optional[str]): A cursor representing the position of the log chunk to fetch
            max_bytes (Optional[int]): A limit on the size of the log chunk to fetch

        Returns:
            CapturedLogData
        """

    @abstractmethod
    def get_contextual_log_metadata(self, log_key: List[str]) -> CapturedLogMetadata:
        """Returns the metadata of the captured logs for a given log key, including
        displayable information on where the logs are persisted.

        Args:
            log_key (List[String]): The log key identifying the captured logs

        Returns:
            CapturedLogMetadata
        """

    @abstractmethod
    def subscribe(
        self, log_key: List[str], cursor: Optional[str] = None
    ) -> CapturedLogSubscription:
        """Registers an observable object for log data

        Args:
            log_key (List[String]): The log key identifying the captured logs
            cursor (Optional[String]): The string cursor marking the position within the log stream
        Returns:
            ComputeLogSubscription
        """

    @abstractmethod
    def unsubscribe(self, subscription: CapturedLogSubscription):
        """Deregisters an observable object from receiving log updates

        Args:
            subscription (CapturedLogSubscription): subscription object which manages when to send
                back data to the subscriber
        """

    def get_in_progress_log_keys(self, prefix: Optional[List[str]] = None) -> List[List[str]]:
        """Utility method to help with keeping track of the set of in-progress capture.  Helpful for
        streaming updates for block-upload captured log managers"""
        return []

    def build_log_key_for_run(self, run_id, step_key):
        """Legacy adapter to translate run_id/key to captured log manager-based log_key"""
        return [run_id, "compute_logs", step_key]
