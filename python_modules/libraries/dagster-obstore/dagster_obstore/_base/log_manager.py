import os
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Optional, Union

import obstore as obs
from dagster import _check as check
from dagster._core.storage.cloud_storage_compute_log_manager import (
    CloudStorageComputeLogManager,
    PollingComputeLogSubscriptionManager,
)
from dagster._core.storage.compute_log_manager import CapturedLogContext, ComputeIOType
from dagster._core.storage.local_compute_log_manager import (
    IO_TYPE_EXTENSION,
    LocalComputeLogManager,
)
from dagster._serdes import ConfigurableClass, ConfigurableClassData
from dagster._utils import ensure_dir, ensure_file
from obstore.exceptions import NotFoundError  # type: ignore
from typing_extensions import Self

POLLING_INTERVAL = 5


if TYPE_CHECKING:
    from obstore import ListStream, ObjectMeta
    from obstore.store import AzureStore, GCSStore, S3Store


class BaseCloudStorageComputeLogManager(CloudStorageComputeLogManager, ConfigurableClass):
    def __init__(
        self,
        inst_data: Optional[ConfigurableClassData] = None,
    ):
        self._prefix: str
        self._local_manager: LocalComputeLogManager
        self._subscription_manager: PollingComputeLogSubscriptionManager
        self._inst_data: Optional[ConfigurableClassData]
        self._skip_empty_files: bool
        self._upload_interval: Optional[int]
        self._show_url_only: Optional[bool]
        self._store: Union[S3Store, AzureStore, GCSStore]

    @property
    def inst_data(self):
        return self._inst_data

    @classmethod
    def from_config_value(
        cls, inst_data: ConfigurableClassData, config_value: Mapping[str, Any]
    ) -> Self:
        return cls(inst_data=inst_data, **config_value)

    @property
    def local_manager(self) -> LocalComputeLogManager:
        return self._local_manager

    @property
    def upload_interval(self) -> Optional[int]:
        return self._upload_interval if self._upload_interval else None

    def _clean_prefix(self, prefix):
        parts = prefix.split("/")
        return "/".join([part for part in parts if part])

    def _resolve_path_for_namespace(self, namespace):
        return [self._prefix, "storage", *namespace]

    def _blob_key(self, log_key: Sequence[str], io_type: ComputeIOType, partial=False):
        check.inst_param(io_type, "io_type", ComputeIOType)
        extension = IO_TYPE_EXTENSION[io_type]
        [*namespace, filebase] = log_key
        filename = f"{filebase}.{extension}"
        if partial:
            filename = f"{filename}.partial"
        paths = [*self._resolve_path_for_namespace(namespace), filename]
        return "/".join(paths)

    def delete_logs(
        self, log_key: Optional[Sequence[str]] = None, prefix: Optional[Sequence[str]] = None
    ):
        self.local_manager.delete_logs(log_key=log_key, prefix=prefix)

        blob_keys_to_remove = None
        if log_key:
            blob_keys_to_remove = [
                self._blob_key(log_key, ComputeIOType.STDOUT),
                self._blob_key(log_key, ComputeIOType.STDERR),
                self._blob_key(log_key, ComputeIOType.STDOUT, partial=True),
                self._blob_key(log_key, ComputeIOType.STDERR, partial=True),
            ]
        elif prefix:
            # add the trailing '' to make sure that ['a'] does not match ['apple']
            blob_prefix = "/".join([self._prefix, "storage", *prefix, ""])
            chunk_streams: ListStream[list[ObjectMeta]] = obs.list(
                self._store, prefix=blob_prefix, return_arrow=False
            )
            blob_keys_to_remove = []
            for chunk in chunk_streams:
                chunk: list[ObjectMeta]
                for item in chunk:
                    blob_keys_to_remove.append(item["path"])

        else:
            check.failed("Must pass in either `log_key` or `prefix` argument to delete_logs")

        if blob_keys_to_remove:
            obs.delete(store=self._store, paths=blob_keys_to_remove)

    def download_url_for_type(
        self, log_key: Sequence[str], io_type: ComputeIOType
    ) -> Optional[str]:
        if not self.is_capture_complete(log_key):
            return None
        from datetime import timedelta

        blob_key = self._blob_key(log_key, io_type)
        return obs.sign(self._store, "GET", paths=blob_key, expires_in=timedelta(hours=1))

    def cloud_storage_has_logs(
        self, log_key: Sequence[str], io_type: ComputeIOType, partial: bool = False
    ) -> bool:
        blob_key = self._blob_key(log_key, io_type, partial=partial)
        try:
            obs.head(self._store, path=blob_key)
        except (FileNotFoundError, NotFoundError):
            return False
        return True

    def upload_to_cloud_storage(
        self, log_key: Sequence[str], io_type: ComputeIOType, partial=False
    ):
        path = self.local_manager.get_captured_local_path(log_key, IO_TYPE_EXTENSION[io_type])
        ensure_file(path)

        if (self._skip_empty_files or partial) and os.stat(path).st_size == 0:
            return

        blob_key = self._blob_key(log_key, io_type, partial=partial)
        with open(path, "rb") as data:
            obs.put(self._store, blob_key, file=data, attributes={"ContentType": "text/plain"})

    def download_from_cloud_storage(
        self, log_key: Sequence[str], io_type: ComputeIOType, partial=False
    ):
        path = self._local_manager.get_captured_local_path(
            log_key, IO_TYPE_EXTENSION[io_type], partial=partial
        )
        ensure_dir(os.path.dirname(path))
        blob_key = self._blob_key(log_key, io_type, partial=partial)
        with open(path, "wb") as fileobj:
            file_bytes = obs.get(self._store, blob_key).bytes()
            fileobj.write(file_bytes)

    def get_log_keys_for_log_key_prefix(
        self, log_key_prefix: Sequence[str], io_type: ComputeIOType
    ) -> Sequence[Sequence[str]]:
        directory = self._resolve_path_for_namespace(log_key_prefix)
        chunk_streams: ListStream[list[ObjectMeta]] = obs.list(
            self._store, prefix="/".join(directory)
        )

        results = []
        list_key_prefix = list(log_key_prefix)
        for chunk in chunk_streams:
            chunk: list[ObjectMeta]
            for item in chunk:
                full_key = item["path"]
                filename, obj_io_type = full_key.split("/")[-1].split(".")
                if obj_io_type != IO_TYPE_EXTENSION[io_type]:
                    continue
                results.append(list_key_prefix + [filename])
        return results

    def on_subscribe(self, subscription):
        self._subscription_manager.add_subscription(subscription)

    def on_unsubscribe(self, subscription):
        self._subscription_manager.remove_subscription(subscription)

    def dispose(self):
        self._subscription_manager.dispose()
        self._local_manager.dispose()

    @contextmanager
    def capture_logs(self, log_key: Sequence[str]) -> Iterator[CapturedLogContext]:
        with super().capture_logs(log_key) as local_context:
            if not self._show_url_only:
                yield local_context
            else:
                yield CapturedLogContext(
                    local_context.log_key,
                )
