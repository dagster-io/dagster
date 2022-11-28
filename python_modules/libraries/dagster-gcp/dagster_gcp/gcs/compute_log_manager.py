import json
import os
from typing import Optional, Sequence

from google.cloud import storage  # type: ignore

import dagster._seven as seven
from dagster import Field, StringSource
from dagster import _check as check
from dagster._config.config_type import Noneable
from dagster._core.storage.cloud_storage_compute_log_manager import (
    CloudStorageComputeLogManager,
    PollingComputeLogSubscriptionManager,
)
from dagster._core.storage.compute_log_manager import ComputeIOType
from dagster._core.storage.local_compute_log_manager import (
    IO_TYPE_EXTENSION,
    LocalComputeLogManager,
)
from dagster._serdes import ConfigurableClass, ConfigurableClassData
from dagster._utils import ensure_dir, ensure_file


class GCSComputeLogManager(CloudStorageComputeLogManager, ConfigurableClass):
    """Logs op compute function stdout and stderr to GCS.

    Users should not instantiate this class directly. Instead, use a YAML block in ``dagster.yaml``
    such as the following:

    .. code-block:: YAML

        compute_logs:
          module: dagster_gcp.gcs.compute_log_manager
          class: GCSComputeLogManager
          config:
            bucket: "mycorp-dagster-compute-logs"
            local_dir: "/tmp/cool"
            prefix: "dagster-test-"
            upload_interval: 30

    Args:
        bucket (str): The name of the gcs bucket to which to log.
        local_dir (Optional[str]): Path to the local directory in which to stage logs. Default:
            ``dagster._seven.get_system_temp_directory()``.
        prefix (Optional[str]): Prefix for the log file keys.
        json_credentials_envvar (Optional[str]): Env variable that contain the JSON with a private key
            and other credentials information. If this is set GOOGLE_APPLICATION_CREDENTIALS will be ignored.
            Can be used when the private key cannot be used as a file.
        upload_interval: (Optional[int]): Interval in seconds to upload partial log files to GCS. By default, will only upload when the capture is complete.
        inst_data (Optional[ConfigurableClassData]): Serializable representation of the compute
            log manager when newed up from config.
    """

    def __init__(
        self,
        bucket,
        local_dir=None,
        inst_data=None,
        prefix="dagster",
        json_credentials_envvar=None,
        upload_interval=None,
    ):
        self._bucket_name = check.str_param(bucket, "bucket")
        self._prefix = self._clean_prefix(check.str_param(prefix, "prefix"))

        if json_credentials_envvar:
            json_info_str = os.environ.get(json_credentials_envvar)
            credentials_info = json.loads(json_info_str)
            self._bucket = (
                storage.Client()
                .from_service_account_info(credentials_info)
                .bucket(self._bucket_name)
            )
        else:
            self._bucket = storage.Client().bucket(self._bucket_name)

        # Check if the bucket exists
        check.invariant(self._bucket.exists())

        # proxy calls to local compute log manager (for subscriptions, etc)
        if not local_dir:
            local_dir = seven.get_system_temp_directory()

        self._upload_interval = check.opt_int_param(upload_interval, "upload_interval")
        self._local_manager = LocalComputeLogManager(local_dir)
        self._subscription_manager = PollingComputeLogSubscriptionManager(self)
        self._inst_data = check.opt_inst_param(inst_data, "inst_data", ConfigurableClassData)

    @property
    def inst_data(self):
        return self._inst_data

    @classmethod
    def config_type(cls):
        return {
            "bucket": StringSource,
            "local_dir": Field(StringSource, is_required=False),
            "prefix": Field(StringSource, is_required=False, default_value="dagster"),
            "json_credentials_envvar": Field(StringSource, is_required=False),
            "upload_interval": Field(Noneable(int), is_required=False, default_value=None),
        }

    @staticmethod
    def from_config_value(inst_data, config_value):
        return GCSComputeLogManager(inst_data=inst_data, **config_value)

    @property
    def local_manager(self) -> LocalComputeLogManager:
        return self._local_manager

    @property
    def upload_interval(self) -> Optional[int]:
        return self._upload_interval if self._upload_interval else None

    def _clean_prefix(self, prefix):
        parts = prefix.split("/")
        return "/".join([part for part in parts if part])

    def _gcs_key(self, log_key, io_type, partial=False):
        check.inst_param(io_type, "io_type", ComputeIOType)
        extension = IO_TYPE_EXTENSION[io_type]
        [*namespace, filebase] = log_key
        filename = f"{filebase}.{extension}"
        if partial:
            filename = f"{filename}.partial"
        paths = [self._prefix, "storage", *namespace, filename]
        return "/".join(paths)

    def delete_logs(
        self, log_key: Optional[Sequence[str]] = None, prefix: Optional[Sequence[str]] = None
    ):
        self._local_manager.delete_logs(log_key, prefix)
        if log_key:
            gcs_keys_to_remove = [
                self._gcs_key(log_key, ComputeIOType.STDOUT),
                self._gcs_key(log_key, ComputeIOType.STDERR),
                self._gcs_key(log_key, ComputeIOType.STDOUT, partial=True),
                self._gcs_key(log_key, ComputeIOType.STDERR, partial=True),
            ]
            # if the blob doesn't exist, do nothing instead of raising a not found exception
            self._bucket.delete_blobs(gcs_keys_to_remove, on_error=lambda _: None)
        elif prefix:
            # add the trailing '/' to make sure that ['a'] does not match ['apple']
            delete_prefix = "/".join([self._prefix, "storage", *prefix, ""])
            to_delete = self._bucket.list_blobs(prefix=delete_prefix)
            self._bucket.delete_blobs(list(to_delete))
        else:
            check.failed("Must pass in either `log_key` or `prefix` argument to delete_logs")

    def download_url_for_type(self, log_key: Sequence[str], io_type: ComputeIOType):
        if not self.is_capture_complete(log_key):
            return None

        gcs_key = self._gcs_key(log_key, io_type)
        return self._bucket.blob(gcs_key).generate_signed_url(
            expiration=3600  # match S3 default expiration
        )

    def display_path_for_type(self, log_key: Sequence[str], io_type: ComputeIOType):
        if not self.is_capture_complete(log_key):
            return self.local_manager.get_captured_local_path(log_key, IO_TYPE_EXTENSION[io_type])
        gcs_key = self._gcs_key(log_key, io_type)
        return f"gs://{self._bucket_name}/{gcs_key}"

    def cloud_storage_has_logs(
        self, log_key: Sequence[str], io_type: ComputeIOType, partial: bool = False
    ) -> bool:
        gcs_key = self._gcs_key(log_key, io_type, partial)
        return self._bucket.blob(gcs_key).exists()

    def upload_to_cloud_storage(
        self, log_key: Sequence[str], io_type: ComputeIOType, partial=False
    ):
        path = self.local_manager.get_captured_local_path(log_key, IO_TYPE_EXTENSION[io_type])
        ensure_file(path)

        if partial and os.stat(path).st_size == 0:
            return

        gcs_key = self._gcs_key(log_key, io_type, partial=partial)
        with open(path, "rb") as data:
            self._bucket.blob(gcs_key).upload_from_file(data)

    def download_from_cloud_storage(
        self, log_key: Sequence[str], io_type: ComputeIOType, partial=False
    ):
        path = self.local_manager.get_captured_local_path(
            log_key, IO_TYPE_EXTENSION[io_type], partial=partial
        )
        ensure_dir(os.path.dirname(path))

        gcs_key = self._gcs_key(log_key, io_type, partial=partial)
        with open(path, "wb") as fileobj:
            self._bucket.blob(gcs_key).download_to_file(fileobj)

    def on_subscribe(self, subscription):
        self._subscription_manager.add_subscription(subscription)

    def on_unsubscribe(self, subscription):
        self._subscription_manager.remove_subscription(subscription)

    def dispose(self):
        self._subscription_manager.dispose()
        self._local_manager.dispose()
