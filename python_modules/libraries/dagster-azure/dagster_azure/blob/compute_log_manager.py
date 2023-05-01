import os
from contextlib import contextmanager
from typing import Any, Mapping, Optional, Sequence

import dagster._seven as seven
from azure.identity import DefaultAzureCredential
from dagster import (
    Field,
    Noneable,
    Permissive,
    StringSource,
    _check as check,
)
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
from typing_extensions import Self

from .utils import create_blob_client, generate_blob_sas


class AzureBlobComputeLogManager(CloudStorageComputeLogManager, ConfigurableClass):
    """Logs op compute function stdout and stderr to Azure Blob Storage.

    This is also compatible with Azure Data Lake Storage.

    Users should not instantiate this class directly. Instead, use a YAML block in ``dagster.yaml``
    such as the following:

    .. code-block:: YAML

        compute_logs:
          module: dagster_azure.blob.compute_log_manager
          class: AzureBlobComputeLogManager
          config:
            storage_account: my-storage-account
            container: my-container
            credential: sas-token-or-secret-key
            default_azure_credential:
              exclude_environment_credential: true
            prefix: "dagster-test-"
            local_dir: "/tmp/cool"
            upload_interval: 30

    Args:
        storage_account (str): The storage account name to which to log.
        container (str): The container (or ADLS2 filesystem) to which to log.
        secret_key (Optional[str]): Secret key for the storage account. SAS tokens are not
            supported because we need a secret key to generate a SAS token for a download URL.
        default_azure_credential (Optional[dict]): Use and configure DefaultAzureCredential.
            Cannot be used with sas token or secret key config.
        local_dir (Optional[str]): Path to the local directory in which to stage logs. Default:
            ``dagster._seven.get_system_temp_directory()``.
        prefix (Optional[str]): Prefix for the log file keys.
        upload_interval: (Optional[int]): Interval in seconds to upload partial log files blob storage. By default, will only upload when the capture is complete.
        inst_data (Optional[ConfigurableClassData]): Serializable representation of the compute
            log manager when newed up from config.
    """

    def __init__(
        self,
        storage_account,
        container,
        secret_key=None,
        local_dir=None,
        inst_data: Optional[ConfigurableClassData] = None,
        prefix="dagster",
        upload_interval=None,
        default_azure_credential=None,
    ):
        self._storage_account = check.str_param(storage_account, "storage_account")
        self._container = check.str_param(container, "container")
        self._blob_prefix = self._clean_prefix(check.str_param(prefix, "prefix"))
        self._default_azure_credential = check.opt_dict_param(
            default_azure_credential, "default_azure_credential"
        )
        check.opt_str_param(secret_key, "secret_key")
        check.invariant(
            secret_key is not None or default_azure_credential is not None,
            "Missing config: need to provide one of secret_key or default_azure_credential",
        )

        if default_azure_credential is None:
            self._blob_client = create_blob_client(storage_account, secret_key)
        else:
            credential = DefaultAzureCredential(**self._default_azure_credential)
            self._blob_client = create_blob_client(storage_account, credential)

        self._container_client = self._blob_client.get_container_client(container)
        self._download_urls = {}

        # proxy calls to local compute log manager (for subscriptions, etc)
        if not local_dir:
            local_dir = seven.get_system_temp_directory()

        self._local_manager = LocalComputeLogManager(local_dir)
        self._subscription_manager = PollingComputeLogSubscriptionManager(self)
        self._upload_interval = check.opt_int_param(upload_interval, "upload_interval")
        self._inst_data = check.opt_inst_param(inst_data, "inst_data", ConfigurableClassData)

    @contextmanager
    def _watch_logs(self, dagster_run, step_key=None):
        # proxy watching to the local compute log manager, interacting with the filesystem
        with self.local_manager._watch_logs(dagster_run, step_key):  # noqa: SLF001
            yield

    @property
    def inst_data(self):
        return self._inst_data

    @classmethod
    def config_type(cls):
        return {
            "storage_account": StringSource,
            "container": StringSource,
            "secret_key": Field(StringSource, is_required=False),
            "default_azure_credential": Field(
                Noneable(Permissive(description="keyword arguments for DefaultAzureCredential")),
                is_required=False,
                default_value=None,
            ),
            "local_dir": Field(StringSource, is_required=False),
            "prefix": Field(StringSource, is_required=False, default_value="dagster"),
            "upload_interval": Field(Noneable(int), is_required=False, default_value=None),
        }

    @classmethod
    def from_config_value(
        cls, inst_data: ConfigurableClassData, config_value: Mapping[str, Any]
    ) -> Self:
        return AzureBlobComputeLogManager(inst_data=inst_data, **config_value)

    @property
    def local_manager(self) -> LocalComputeLogManager:
        return self._local_manager

    @property
    def upload_interval(self) -> Optional[int]:
        return self._upload_interval if self._upload_interval else None

    def _clean_prefix(self, prefix):
        parts = prefix.split("/")
        return "/".join([part for part in parts if part])

    def _blob_key(self, log_key, io_type, partial=False):
        check.inst_param(io_type, "io_type", ComputeIOType)
        extension = IO_TYPE_EXTENSION[io_type]
        [*namespace, filebase] = log_key
        filename = f"{filebase}.{extension}"
        if partial:
            filename = f"{filename}.partial"
        paths = [self._blob_prefix, "storage", *namespace, filename]
        return "/".join(paths)  # blob path delimiter

    def delete_logs(
        self, log_key: Optional[Sequence[str]] = None, prefix: Optional[Sequence[str]] = None
    ):
        self.local_manager.delete_logs(log_key=log_key, prefix=prefix)
        if log_key:
            prefix_path = "/".join([self._blob_prefix, "storage", *log_key])
        elif prefix:
            # add the trailing '/' to make sure that ['a'] does not match ['apple']
            prefix_path = "/".join([self._blob_prefix, "storage", *prefix, ""])
        else:
            prefix_path = None

        blob_list = {
            b.name for b in list(self._container_client.list_blobs(name_starts_with=prefix_path))
        }

        to_remove = None
        if log_key:
            # filter to the known set of keys
            known_keys = [
                self._blob_key(log_key, ComputeIOType.STDOUT),
                self._blob_key(log_key, ComputeIOType.STDERR),
                self._blob_key(log_key, ComputeIOType.STDOUT, partial=True),
                self._blob_key(log_key, ComputeIOType.STDERR, partial=True),
            ]
            to_remove = [key for key in known_keys if key in blob_list]
        elif prefix:
            to_remove = list(blob_list)
        else:
            check.failed("Must pass in either `log_key` or `prefix` argument to delete_logs")

        if to_remove:
            self._container_client.delete_blobs(*to_remove)

    def download_url_for_type(self, log_key: Sequence[str], io_type: ComputeIOType):
        if not self.is_capture_complete(log_key):
            return None

        blob_key = self._blob_key(log_key, io_type)
        if blob_key in self._download_urls:
            return self._download_urls[blob_key]
        blob = self._container_client.get_blob_client(blob_key)
        sas = generate_blob_sas(
            self._storage_account,
            self._container,
            blob_key,
            account_key=self._blob_client.credential.account_key,
        )
        url = blob.url + sas
        self._download_urls[blob_key] = url
        return url

    def display_path_for_type(self, log_key: Sequence[str], io_type: ComputeIOType):
        if not self.is_capture_complete(log_key):
            return self.local_manager.get_captured_local_path(log_key, IO_TYPE_EXTENSION[io_type])

        blob_key = self._blob_key(log_key, io_type)
        return f"https://{self._storage_account}.blob.core.windows.net/{self._container}/{blob_key}"

    def cloud_storage_has_logs(
        self, log_key: Sequence[str], io_type: ComputeIOType, partial: bool = False
    ) -> bool:
        blob_key = self._blob_key(log_key, io_type, partial=partial)
        blob_objects = self._container_client.list_blobs(blob_key)
        exact_matches = [blob for blob in blob_objects if blob.name == blob_key]
        return len(exact_matches) > 0

    def upload_to_cloud_storage(
        self, log_key: Sequence[str], io_type: ComputeIOType, partial=False
    ):
        path = self.local_manager.get_captured_local_path(log_key, IO_TYPE_EXTENSION[io_type])
        ensure_file(path)
        blob_key = self._blob_key(log_key, io_type, partial=partial)
        with open(path, "rb") as data:
            blob = self._container_client.get_blob_client(blob_key)
            blob.upload_blob(data)

    def download_from_cloud_storage(
        self, log_key: Sequence[str], io_type: ComputeIOType, partial=False
    ):
        path = self.local_manager.get_captured_local_path(
            log_key, IO_TYPE_EXTENSION[io_type], partial=partial
        )
        ensure_dir(os.path.dirname(path))
        blob_key = self._blob_key(log_key, io_type, partial=partial)
        with open(path, "wb") as fileobj:
            blob = self._container_client.get_blob_client(blob_key)
            blob.download_blob().readinto(fileobj)

    def on_subscribe(self, subscription):
        self._subscription_manager.add_subscription(subscription)

    def on_unsubscribe(self, subscription):
        self._subscription_manager.remove_subscription(subscription)
