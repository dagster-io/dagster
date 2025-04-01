import os
import shutil
import sys
from collections import defaultdict
from collections.abc import Generator, Iterator, Mapping, Sequence
from contextlib import contextmanager
from pathlib import Path
from typing import IO, Final, Optional

from dagster_shared.seven import json
from watchdog.events import PatternMatchingEventHandler
from watchdog.observers.polling import PollingObserver

from dagster import (
    Field,
    Float,
    StringSource,
    _check as check,
)
from dagster._config.config_schema import UserConfigSchema
from dagster._core.execution.compute_logs import mirror_stream_to_file
from dagster._core.storage.compute_log_manager import (
    CapturedLogContext,
    CapturedLogData,
    CapturedLogMetadata,
    CapturedLogSubscription,
    ComputeIOType,
    ComputeLogManager,
)
from dagster._serdes import ConfigurableClass, ConfigurableClassData
from dagster._utils import ensure_dir, ensure_file, touch_file
from dagster._utils.security import non_secure_md5_hash_str

DEFAULT_WATCHDOG_POLLING_TIMEOUT: Final = 2.5

IO_TYPE_EXTENSION: Final[Mapping[ComputeIOType, str]] = {
    ComputeIOType.STDOUT: "out",
    ComputeIOType.STDERR: "err",
}

MAX_FILENAME_LENGTH: Final = 255


class LocalComputeLogManager(ComputeLogManager, ConfigurableClass):
    """Stores copies of stdout & stderr for each compute step locally on disk."""

    def __init__(
        self,
        base_dir: str,
        polling_timeout: Optional[float] = None,
        inst_data: Optional[ConfigurableClassData] = None,
    ):
        self._base_dir = base_dir
        self._polling_timeout = check.opt_float_param(
            polling_timeout, "polling_timeout", DEFAULT_WATCHDOG_POLLING_TIMEOUT
        )
        self._subscription_manager = LocalComputeLogSubscriptionManager(self)
        self._inst_data = check.opt_inst_param(inst_data, "inst_data", ConfigurableClassData)

    @property
    def inst_data(self) -> Optional[ConfigurableClassData]:
        return self._inst_data

    @property
    def polling_timeout(self) -> float:
        return self._polling_timeout

    @classmethod
    def config_type(cls) -> UserConfigSchema:
        return {
            "base_dir": StringSource,
            "polling_timeout": Field(Float, is_required=False),
        }

    @classmethod
    def from_config_value(
        cls, inst_data: Optional[ConfigurableClassData], config_value
    ) -> "LocalComputeLogManager":
        return LocalComputeLogManager(inst_data=inst_data, **config_value)

    @contextmanager
    def capture_logs(self, log_key: Sequence[str]) -> Generator[CapturedLogContext, None, None]:
        outpath = self.get_captured_local_path(log_key, IO_TYPE_EXTENSION[ComputeIOType.STDOUT])
        errpath = self.get_captured_local_path(log_key, IO_TYPE_EXTENSION[ComputeIOType.STDERR])
        with mirror_stream_to_file(sys.stdout, outpath), mirror_stream_to_file(sys.stderr, errpath):
            yield CapturedLogContext(log_key)

        # leave artifact on filesystem so that we know the capture is completed
        touch_file(self.complete_artifact_path(log_key))

    @contextmanager
    def open_log_stream(
        self, log_key: Sequence[str], io_type: ComputeIOType
    ) -> Iterator[Optional[IO]]:
        path = self.get_captured_local_path(log_key, IO_TYPE_EXTENSION[io_type])
        ensure_file(path)
        with open(path, "+a", encoding="utf-8") as f:
            yield f

    def is_capture_complete(self, log_key: Sequence[str]) -> bool:
        return os.path.exists(self.complete_artifact_path(log_key))

    def get_log_data(
        self, log_key: Sequence[str], cursor: Optional[str] = None, max_bytes: Optional[int] = None
    ) -> CapturedLogData:
        stdout_cursor, stderr_cursor = self.parse_cursor(cursor)
        stdout, stdout_offset = self.get_log_data_for_type(
            log_key, ComputeIOType.STDOUT, offset=stdout_cursor, max_bytes=max_bytes
        )
        stderr, stderr_offset = self.get_log_data_for_type(
            log_key, ComputeIOType.STDERR, offset=stderr_cursor, max_bytes=max_bytes
        )
        return CapturedLogData(
            log_key=log_key,
            stdout=stdout,
            stderr=stderr,
            cursor=self.build_cursor(stdout_offset, stderr_offset),
        )

    def get_log_metadata(self, log_key: Sequence[str]) -> CapturedLogMetadata:
        return CapturedLogMetadata(
            stdout_location=self.get_captured_local_path(
                log_key, IO_TYPE_EXTENSION[ComputeIOType.STDOUT]
            ),
            stderr_location=self.get_captured_local_path(
                log_key, IO_TYPE_EXTENSION[ComputeIOType.STDERR]
            ),
            stdout_download_url=self.get_captured_log_download_url(log_key, ComputeIOType.STDOUT),
            stderr_download_url=self.get_captured_log_download_url(log_key, ComputeIOType.STDERR),
        )

    def delete_logs(
        self, log_key: Optional[Sequence[str]] = None, prefix: Optional[Sequence[str]] = None
    ):
        if log_key:
            paths = [
                self.get_captured_local_path(log_key, IO_TYPE_EXTENSION[ComputeIOType.STDOUT]),
                self.get_captured_local_path(log_key, IO_TYPE_EXTENSION[ComputeIOType.STDERR]),
                self.get_captured_local_path(
                    log_key, IO_TYPE_EXTENSION[ComputeIOType.STDOUT], partial=True
                ),
                self.get_captured_local_path(
                    log_key, IO_TYPE_EXTENSION[ComputeIOType.STDERR], partial=True
                ),
                self.get_captured_local_path(log_key, "complete"),
            ]
            for path in paths:
                if os.path.exists(path) and os.path.isfile(path):
                    os.remove(path)
        elif prefix:
            dir_to_delete = os.path.join(self._base_dir, *prefix)
            if os.path.exists(dir_to_delete) and os.path.isdir(dir_to_delete):
                # recursively delete all files in dir
                shutil.rmtree(dir_to_delete)
        else:
            check.failed("Must pass in either `log_key` or `prefix` argument to delete_logs")

    def get_log_data_for_type(
        self,
        log_key: Sequence[str],
        io_type: ComputeIOType,
        offset: Optional[int] = 0,
        max_bytes: Optional[int] = None,
    ):
        path = self.get_captured_local_path(log_key, IO_TYPE_EXTENSION[io_type])
        return self.read_path(path, offset or 0, max_bytes)

    def complete_artifact_path(self, log_key):
        return self.get_captured_local_path(log_key, "complete")

    def read_path(
        self,
        path: str,
        offset: int = 0,
        max_bytes: Optional[int] = None,
    ):
        if not os.path.exists(path) or not os.path.isfile(path):
            return None, offset

        with open(path, "rb") as f:
            f.seek(offset, os.SEEK_SET)
            if max_bytes is None:
                data = f.read()
            else:
                data = f.read(max_bytes)
            new_offset = f.tell()
        return data, new_offset

    def get_captured_log_download_url(self, log_key, io_type):
        check.inst_param(io_type, "io_type", ComputeIOType)
        url = "/logs"
        for part in log_key:
            url = f"{url}/{part}"

        return f"{url}/{IO_TYPE_EXTENSION[io_type]}"

    def get_captured_local_path(self, log_key: Sequence[str], extension: str, partial=False):
        [*namespace, filebase] = log_key
        filename = f"{filebase}.{extension}"
        if partial:
            filename = f"{filename}.partial"
        if len(filename) > MAX_FILENAME_LENGTH:
            filename = "{}.{}".format(non_secure_md5_hash_str(filebase.encode("utf-8")), extension)
        base_dir_path = Path(self._base_dir).resolve()
        log_path = base_dir_path.joinpath(*namespace, filename).resolve()
        if base_dir_path not in log_path.parents:
            raise ValueError("Invalid path")
        return str(log_path)

    def subscribe(
        self, log_key: Sequence[str], cursor: Optional[str] = None
    ) -> CapturedLogSubscription:
        subscription = CapturedLogSubscription(self, log_key, cursor)
        self._subscription_manager.add_subscription(subscription)
        return subscription

    def unsubscribe(self, subscription):
        self._subscription_manager.remove_subscription(subscription)

    def get_log_keys_for_log_key_prefix(
        self, log_key_prefix: Sequence[str], io_type: ComputeIOType
    ) -> Sequence[Sequence[str]]:
        """Returns the logs keys for a given log key prefix. This is determined by looking at the
        directory defined by the log key prefix and creating a log_key for each file in the directory.
        """
        base_dir_path = Path(self._base_dir).resolve()
        directory = base_dir_path.joinpath(*log_key_prefix)
        objects = directory.iterdir()
        results = []
        list_key_prefix = list(log_key_prefix)

        for obj in objects:
            if obj.is_file() and obj.suffix == "." + IO_TYPE_EXTENSION[io_type]:
                results.append(list_key_prefix + [obj.stem])

        return results

    def dispose(self) -> None:
        self._subscription_manager.dispose()


class LocalComputeLogSubscriptionManager:
    def __init__(self, manager):
        self._manager = manager
        self._subscriptions = defaultdict(list)
        self._watchers = {}
        self._observer = None

    def add_subscription(self, subscription: CapturedLogSubscription) -> None:
        check.inst_param(subscription, "subscription", CapturedLogSubscription)

        if self.is_complete(subscription):
            subscription.fetch()
            subscription.complete()
        else:
            log_key = self._log_key(subscription)
            watch_key = self._watch_key(log_key)
            self._subscriptions[watch_key].append(subscription)
            self.watch(subscription)

    def is_complete(self, subscription: CapturedLogSubscription) -> bool:
        check.inst_param(subscription, "subscription", CapturedLogSubscription)

        return self._manager.is_capture_complete(subscription.log_key)

    def remove_subscription(self, subscription: CapturedLogSubscription) -> None:
        check.inst_param(subscription, "subscription", CapturedLogSubscription)
        log_key = self._log_key(subscription)
        watch_key = self._watch_key(log_key)
        if subscription in self._subscriptions[watch_key]:
            self._subscriptions[watch_key].remove(subscription)
            subscription.complete()

    def _log_key(self, subscription: CapturedLogSubscription) -> Sequence[str]:
        check.inst_param(subscription, "subscription", CapturedLogSubscription)

        return subscription.log_key

    def _watch_key(self, log_key: Sequence[str]) -> str:
        return json.dumps(log_key)

    def remove_all_subscriptions(self, log_key: Sequence[str]) -> None:
        watch_key = self._watch_key(log_key)
        for subscription in self._subscriptions.pop(watch_key, []):
            subscription.complete()

    def watch(self, subscription: CapturedLogSubscription) -> None:
        log_key = self._log_key(subscription)
        watch_key = self._watch_key(log_key)
        if watch_key in self._watchers:
            return

        update_paths = [
            self._manager.get_captured_local_path(log_key, IO_TYPE_EXTENSION[ComputeIOType.STDOUT]),
            self._manager.get_captured_local_path(log_key, IO_TYPE_EXTENSION[ComputeIOType.STDERR]),
            self._manager.get_captured_local_path(
                log_key, IO_TYPE_EXTENSION[ComputeIOType.STDOUT], partial=True
            ),
            self._manager.get_captured_local_path(
                log_key, IO_TYPE_EXTENSION[ComputeIOType.STDERR], partial=True
            ),
        ]
        complete_paths = [self._manager.complete_artifact_path(log_key)]
        directory = os.path.dirname(
            self._manager.get_captured_local_path(log_key, ComputeIOType.STDERR),
        )

        if not self._observer:
            self._observer = PollingObserver(timeout=self._manager.polling_timeout)
            self._observer.start()

        ensure_dir(directory)

        self._watchers[watch_key] = self._observer.schedule(
            LocalComputeLogFilesystemEventHandler(self, log_key, update_paths, complete_paths),
            str(directory),
        )

    def notify_subscriptions(self, log_key: Sequence[str]) -> None:
        watch_key = self._watch_key(log_key)
        for subscription in self._subscriptions[watch_key]:
            subscription.fetch()

    def unwatch(self, log_key: Sequence[str], handler) -> None:
        watch_key = self._watch_key(log_key)
        if watch_key in self._watchers:
            self._observer.remove_handler_for_watch(handler, self._watchers[watch_key])  # type: ignore
        del self._watchers[watch_key]

    def dispose(self) -> None:
        if self._observer:
            self._observer.stop()
            self._observer.join(15)


class LocalComputeLogFilesystemEventHandler(PatternMatchingEventHandler):
    def __init__(self, manager, log_key, update_paths, complete_paths):
        self.manager = manager
        self.log_key = log_key
        self.update_paths = update_paths
        self.complete_paths = complete_paths
        patterns = update_paths + complete_paths
        super().__init__(patterns=patterns)

    def on_created(self, event):
        if event.src_path in self.complete_paths:
            self.manager.remove_all_subscriptions(self.log_key)
            self.manager.unwatch(self.log_key, self)

    def on_modified(self, event):
        if event.src_path in self.update_paths:
            self.manager.notify_subscriptions(self.log_key)
