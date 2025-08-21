import json
import logging
import os
import sys
import tempfile
import threading
import time
from abc import abstractmethod
from collections import defaultdict
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from typing import IO, Optional

from dagster._core.instance import T_DagsterInstance
from dagster._core.storage.compute_log_manager import (
    CapturedLogContext,
    CapturedLogMetadata,
    CapturedLogSubscription,
    ComputeIOType,
    ComputeLogManager,
)
from dagster._core.storage.local_compute_log_manager import (
    IO_TYPE_EXTENSION,
    LocalComputeLogManager,
)
from dagster._utils import ensure_file
from dagster._utils.error import serializable_error_info_from_exc_info

SUBSCRIPTION_POLLING_INTERVAL = 5
DEFAULT_TRUNCATE_COMPUTE_LOGS_UPLOAD_BYTES = str(50 * 1024 * 1024)  # 50MB
logger = logging.getLogger("dagster.compute_log_manager")


class CloudStorageComputeLogManager(ComputeLogManager[T_DagsterInstance]):
    """Abstract class that uses the local compute log manager to capture logs and stores them in
    remote cloud storage.
    """

    @property
    @abstractmethod
    def local_manager(self) -> LocalComputeLogManager:
        """Returns a LocalComputeLogManager."""

    @property
    @abstractmethod
    def upload_interval(self) -> Optional[int]:
        """Returns the interval in which partial compute logs are uploaded to cloud storage."""

    @abstractmethod
    def delete_logs(
        self, log_key: Optional[Sequence[str]] = None, prefix: Optional[Sequence[str]] = None
    ) -> None:
        """Deletes logs for a given log_key or prefix."""

    @abstractmethod
    def download_url_for_type(
        self, log_key: Sequence[str], io_type: ComputeIOType
    ) -> Optional[str]:
        """Calculates a download url given a log key and compute io type."""

    @abstractmethod
    def display_path_for_type(self, log_key: Sequence[str], io_type: ComputeIOType) -> str:
        """Returns a display path given a log key and compute io type."""

    @abstractmethod
    def cloud_storage_has_logs(
        self, log_key: Sequence[str], io_type: ComputeIOType, partial: bool = False
    ) -> bool:
        """Returns whether the cloud storage contains logs for a given log key."""

    @abstractmethod
    def upload_to_cloud_storage(
        self, log_key: Sequence[str], io_type: ComputeIOType, partial: bool = False
    ) -> None:
        """Uploads the logs for a given log key from local storage to cloud storage."""

    def download_from_cloud_storage(
        self, log_key: Sequence[str], io_type: ComputeIOType, partial: bool = False
    ) -> None:
        """Downloads the logs for a given log key from cloud storage to local storage."""

    @contextmanager
    def capture_logs(self, log_key: Sequence[str]) -> Iterator[CapturedLogContext]:
        with self._poll_for_local_upload(log_key):
            with self.local_manager.capture_logs(log_key) as context:
                yield context
        self._on_capture_complete(log_key)

    @contextmanager
    def open_log_stream(
        self, log_key: Sequence[str], io_type: ComputeIOType
    ) -> Iterator[Optional[IO]]:
        with self.local_manager.open_log_stream(log_key, io_type) as f:
            yield f
        self._on_capture_complete(log_key)

    def _on_capture_complete(self, log_key: Sequence[str]):
        self.upload_to_cloud_storage(log_key, ComputeIOType.STDOUT)
        self.upload_to_cloud_storage(log_key, ComputeIOType.STDERR)
        try:
            self.local_manager.delete_logs(log_key=log_key)
        except Exception:
            sys.stderr.write(
                f"Exception deleting local logs after capture complete: {serializable_error_info_from_exc_info(sys.exc_info())}\n"
            )

    def is_capture_complete(self, log_key: Sequence[str]) -> bool:
        if self.local_manager.is_capture_complete(log_key):
            return True
        # check remote storage
        return self.cloud_storage_has_logs(log_key, ComputeIOType.STDERR)

    def get_log_data_for_type(
        self,
        log_key: Sequence[str],
        io_type: ComputeIOType,
        offset: int,
        max_bytes: Optional[int],
    ) -> tuple[Optional[bytes], int]:
        if self.has_local_file(log_key, io_type):
            local_path = self.local_manager.get_captured_local_path(
                log_key, IO_TYPE_EXTENSION[io_type]
            )
            return self.local_manager.read_path(local_path, offset=offset, max_bytes=max_bytes)
        if self.cloud_storage_has_logs(log_key, io_type):
            self.download_from_cloud_storage(log_key, io_type)
            local_path = self.local_manager.get_captured_local_path(
                log_key, IO_TYPE_EXTENSION[io_type]
            )
            return self.local_manager.read_path(local_path, offset=offset, max_bytes=max_bytes)
        if self.cloud_storage_has_logs(log_key, io_type, partial=True):
            self.download_from_cloud_storage(log_key, io_type, partial=True)
            local_path = self.local_manager.get_captured_local_path(
                log_key, IO_TYPE_EXTENSION[io_type], partial=True
            )
            return self.local_manager.read_path(local_path, offset=offset, max_bytes=max_bytes)

        return None, offset

    def get_log_metadata(self, log_key: Sequence[str]) -> CapturedLogMetadata:
        return CapturedLogMetadata(
            stdout_location=self.display_path_for_type(log_key, ComputeIOType.STDOUT),
            stderr_location=self.display_path_for_type(log_key, ComputeIOType.STDERR),
            stdout_download_url=self.download_url_for_type(log_key, ComputeIOType.STDOUT),
            stderr_download_url=self.download_url_for_type(log_key, ComputeIOType.STDERR),
        )

    def on_progress(self, log_key):
        # should be called at some interval, to be used for streaming upload implementations
        if self.is_capture_complete(log_key):
            return

        self.upload_to_cloud_storage(log_key, ComputeIOType.STDOUT, partial=True)
        self.upload_to_cloud_storage(log_key, ComputeIOType.STDERR, partial=True)

    def subscribe(
        self, log_key: Sequence[str], cursor: Optional[str] = None
    ) -> CapturedLogSubscription:
        subscription = CapturedLogSubscription(self, log_key, cursor)
        self.on_subscribe(subscription)
        return subscription

    def unsubscribe(self, subscription: CapturedLogSubscription):
        self.on_unsubscribe(subscription)

    def has_local_file(self, log_key: Sequence[str], io_type: ComputeIOType):
        local_path = self.local_manager.get_captured_local_path(log_key, IO_TYPE_EXTENSION[io_type])
        return os.path.exists(local_path)

    def on_subscribe(self, subscription: CapturedLogSubscription):
        pass

    def on_unsubscribe(self, subscription: CapturedLogSubscription):
        pass

    def _should_download(self, log_key: Sequence[str], io_type: ComputeIOType):
        return not self.has_local_file(log_key, io_type) and self.cloud_storage_has_logs(
            log_key, io_type
        )

    @contextmanager
    def _poll_for_local_upload(self, log_key: Sequence[str]) -> Iterator[None]:
        if not self.upload_interval:
            yield
            return

        thread_exit = threading.Event()
        thread = threading.Thread(
            target=_upload_partial_logs,
            args=(self, log_key, thread_exit, self.upload_interval),
            name="upload-watch",
            daemon=True,
        )
        thread.start()
        yield
        thread_exit.set()

    def dispose(self):
        self.local_manager.dispose()


class PollingComputeLogSubscriptionManager:
    def __init__(self, manager):
        self._manager = manager
        self._subscriptions = defaultdict(list)
        self._shutdown_event = None
        self._polling_thread = None

    def _log_key(self, subscription: CapturedLogSubscription) -> Sequence[str]:
        return subscription.log_key

    def _watch_key(self, log_key: Sequence[str]) -> str:
        return json.dumps(log_key)

    def _start_polling_thread(self) -> None:
        if self._polling_thread:
            return

        self._shutdown_event = threading.Event()
        self._polling_thread = threading.Thread(
            target=self._poll,
            args=[self._shutdown_event],
            name="polling-compute-log-subscription",
            daemon=True,
        )
        self._polling_thread.start()

    def _stop_polling_thread(self) -> None:
        if not self._polling_thread:
            return

        old_shutdown_event = self._shutdown_event
        old_shutdown_event.set()  # set to signal to the old thread to die  # type: ignore
        self._polling_thread = None
        self._shutdown_event = None

    def add_subscription(self, subscription: CapturedLogSubscription) -> None:
        if not self._polling_thread:
            self._start_polling_thread()

        if self.is_complete(subscription):
            subscription.fetch()
            subscription.complete()
        else:
            log_key = self._log_key(subscription)
            watch_key = self._watch_key(log_key)
            self._subscriptions[watch_key].append(subscription)

    def is_complete(self, subscription: CapturedLogSubscription) -> bool:
        return self._manager.is_capture_complete(subscription.log_key)

    def remove_subscription(self, subscription: CapturedLogSubscription) -> None:
        log_key = self._log_key(subscription)
        watch_key = self._watch_key(log_key)

        if subscription in self._subscriptions[watch_key]:
            self._subscriptions[watch_key].remove(subscription)
            if len(self._subscriptions[watch_key]) == 0:
                del self._subscriptions[watch_key]
            subscription.complete()

        if not len(self._subscriptions) and self._polling_thread:
            self._stop_polling_thread()

    def remove_all_subscriptions(self, log_key: Sequence[str]) -> None:
        watch_key = self._watch_key(log_key)
        for subscription in self._subscriptions.pop(watch_key, []):
            subscription.complete()

        if not len(self._subscriptions) and self._polling_thread:
            self._stop_polling_thread()

    def notify_subscriptions(self, log_key: Sequence[str]) -> None:
        watch_key = self._watch_key(log_key)
        for subscription in self._subscriptions[watch_key]:
            subscription.fetch()

    def _poll(self, shutdown_event: threading.Event) -> None:
        while True:
            if shutdown_event.is_set():
                return
            # need to do something smarter here that keeps track of updates
            for subscriptions in self._subscriptions.values():
                for subscription in subscriptions:
                    if shutdown_event.is_set():
                        return
                    subscription.fetch()
            time.sleep(SUBSCRIPTION_POLLING_INTERVAL)

    def dispose(self) -> None:
        if self._shutdown_event:
            self._shutdown_event.set()


class TruncatingCloudStorageComputeLogManager(CloudStorageComputeLogManager[T_DagsterInstance]):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._truncated = set()

    @contextmanager
    def _truncate_file(self, path, max_bytes: int) -> Iterator[str]:
        dest = tempfile.NamedTemporaryFile(mode="w+b", delete=False)
        try:
            with open(path, "rb") as src:
                remaining = max_bytes
                bufsize = 64 * 1024

                while remaining:
                    chunk = src.read(min(bufsize, remaining))
                    if not chunk:
                        break
                    dest.write(chunk)
                    remaining -= len(chunk)

                dest.flush()
                dest.close()

                yield dest.name

        finally:
            try:
                os.remove(dest.name)
            except FileNotFoundError:
                pass

    @abstractmethod
    def _upload_file_obj(
        self, data: IO[bytes], log_key: Sequence[str], io_type: ComputeIOType, partial=False
    ):
        pass

    def upload_to_cloud_storage(
        self, log_key: Sequence[str], io_type: ComputeIOType, partial: bool = False
    ) -> None:
        """Uploads the logs for a given log key from local storage to cloud storage."""
        # We've already truncated
        if (tuple(log_key), io_type) in self._truncated:
            logger.debug(f"Compute logs have already been truncated; Skipping upload to {log_key}")
            return

        path = self.local_manager.get_captured_local_path(log_key, IO_TYPE_EXTENSION[io_type])
        ensure_file(path)

        max_bytes = int(
            os.environ.get(
                "DAGSTER_TRUNCATE_COMPUTE_LOGS_UPLOAD_BYTES",
                DEFAULT_TRUNCATE_COMPUTE_LOGS_UPLOAD_BYTES,
            )
        )
        if max_bytes and os.stat(path).st_size >= max_bytes:
            self._truncated.add((tuple(log_key), io_type))
            with self._truncate_file(path, max_bytes=max_bytes) as truncated_path:
                with open(truncated_path, "rb") as data:
                    logger.info(
                        f"Truncating compute logs to {max_bytes} bytes and uploading to {log_key}"
                    )
                    self._upload_file_obj(data, log_key, io_type, partial)
        else:
            with open(path, "rb") as data:
                self._upload_file_obj(data, log_key, io_type, partial)


def _upload_partial_logs(
    compute_log_manager: CloudStorageComputeLogManager,
    log_key: Sequence[str],
    thread_exit: threading.Event,
    interval: int,
) -> None:
    while True:
        time.sleep(interval)
        if thread_exit.is_set() or compute_log_manager.is_capture_complete(log_key):
            return
        compute_log_manager.on_progress(log_key)
