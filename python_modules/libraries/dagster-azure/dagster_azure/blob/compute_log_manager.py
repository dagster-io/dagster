import os
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import dagster_shared.seven as seven
from azure.identity import ClientSecretCredential, DefaultAzureCredential
from azure.storage.blob import BlobSasPermissions, BlobServiceClient, UserDelegationKey
from dagster import (
    Field,
    Noneable,
    Permissive,
    Shape,
    StringSource,
    _check as check,
)
from dagster._core.storage.cloud_storage_compute_log_manager import (
    CloudStorageComputeLogManager,
    PollingComputeLogSubscriptionManager,
)
from dagster._core.storage.compute_log_manager import (
    CapturedLogContext,
    ComputeIOType,
    LogRetrievalShellCommand,
)
from dagster._core.storage.local_compute_log_manager import (
    IO_TYPE_EXTENSION,
    LocalComputeLogManager,
)
from dagster._serdes import ConfigurableClass, ConfigurableClassData
from dagster._utils import ensure_dir, ensure_file
from typing_extensions import Self

from dagster_azure.blob.utils import create_blob_client, generate_blob_sas


class AzureBlobComputeLogManager(CloudStorageComputeLogManager, ConfigurableClass):
    """Logs op compute function stdout and stderr to Azure Blob Storage.

    This is also compatible with Azure Data Lake Storage.

    Users should not instantiate this class directly. Instead, use a YAML block in ``dagster.yaml``. Examples provided below
    will show how to configure with various credentialing schemes.

    Args:
        storage_account (str): The storage account name to which to log.
        container (str): The container (or ADLS2 filesystem) to which to log.
        secret_credential (Optional[dict]): Secret credential for the storage account. This should be
            a dictionary with keys `client_id`, `client_secret`, and `tenant_id`.
        access_key_or_sas_token (Optional[str]): Access key or SAS token for the storage account.
        default_azure_credential (Optional[dict]): Use and configure DefaultAzureCredential.
            Cannot be used with sas token or secret key config.
        local_dir (Optional[str]): Path to the local directory in which to stage logs. Default:
            ``dagster_shared.seven.get_system_temp_directory()``.
        prefix (Optional[str]): Prefix for the log file keys.
        upload_interval (Optional[int]): Interval in seconds to upload partial log files blob storage. By default, will only upload when the capture is complete.
        show_url_only (bool): Only show the URL of the log file in the UI, instead of fetching and displaying the full content. Default False.
        inst_data (Optional[ConfigurableClassData]): Serializable representation of the compute
            log manager when newed up from config.

    Examples:
    Using an Azure Blob Storage account with an `AzureSecretCredential <https://learn.microsoft.com/en-us/python/api/azure-identity/azure.identity.clientsecretcredential?view=azure-python>`_:

    .. code-block:: YAML

        compute_logs:
          module: dagster_azure.blob.compute_log_manager
          class: AzureBlobComputeLogManager
          config:
            storage_account: my-storage-account
            container: my-container
            secret_credential:
              client_id: my-client-id
              client_secret: my-client-secret
              tenant_id: my-tenant-id
            prefix: "dagster-test-"
            local_dir: "/tmp/cool"
            upload_interval: 30
            show_url_only: false

    Using an Azure Blob Storage account with a `DefaultAzureCredential <https://learn.microsoft.com/en-us/python/api/azure-identity/azure.identity.defaultazurecredential?view=azure-python>`_:

    .. code-block:: YAML

        compute_logs:
          module: dagster_azure.blob.compute_log_manager
          class: AzureBlobComputeLogManager
          config:
            storage_account: my-storage-account
            container: my-container
            default_azure_credential:
              exclude_environment_credential: false
            prefix: "dagster-test-"
            local_dir: "/tmp/cool"
            upload_interval: 30
            show_url_only: false

    Using an Azure Blob Storage account with an access key:

    .. code-block:: YAML

        compute_logs:
          module: dagster_azure.blob.compute_log_manager
          class: AzureBlobComputeLogManager
            config:
            storage_account: my-storage-account
            container: my-container
            access_key_or_sas_token: my-access-key
            prefix: "dagster-test-"
            local_dir: "/tmp/cool"
            upload_interval: 30
            show_url_only: false

    """

    def __init__(
        self,
        storage_account: str,
        container: str,
        secret_credential: Optional[dict] = None,
        local_dir: Optional[str] = None,
        inst_data: Optional[ConfigurableClassData] = None,
        prefix: str = "dagster",
        upload_interval: Optional[int] = None,
        default_azure_credential: Optional[dict] = None,
        access_key_or_sas_token: Optional[str] = None,
        show_url_only: bool = False,
    ):
        self._show_url_only = check.bool_param(show_url_only, "show_url_only")
        self._storage_account = check.str_param(storage_account, "storage_account")
        self._container = check.str_param(container, "container")
        self._blob_prefix = self._clean_prefix(check.str_param(prefix, "prefix"))
        self._default_azure_credential = check.opt_dict_param(
            default_azure_credential, "default_azure_credential"
        )
        self._access_key_or_sas_token = check.opt_str_param(
            access_key_or_sas_token, "access_key_or_sas_token"
        )
        check.opt_dict_param(secret_credential, "secret_credential")
        check.opt_dict_param(default_azure_credential, "default_azure_credential")

        if secret_credential is not None:
            self._blob_client = create_blob_client(
                storage_account, ClientSecretCredential(**secret_credential)
            )
        elif self._access_key_or_sas_token:
            self._blob_client = create_blob_client(storage_account, self._access_key_or_sas_token)
        else:
            credential = DefaultAzureCredential(**self._default_azure_credential)
            self._blob_client = create_blob_client(storage_account, credential)

        self._container_client = self._blob_client.get_container_client(container)
        self._download_urls = {}

        # proxy calls to local compute log manager (for subscriptions, etc)
        base_dir: str = local_dir if local_dir else seven.get_system_temp_directory()

        self._local_manager = LocalComputeLogManager(base_dir)
        self._subscription_manager = PollingComputeLogSubscriptionManager(self)
        self._upload_interval = check.opt_int_param(upload_interval, "upload_interval")
        self._inst_data = check.opt_inst_param(inst_data, "inst_data", ConfigurableClassData)

    @property
    def inst_data(self) -> Optional[ConfigurableClassData]:
        return self._inst_data

    @classmethod
    def config_type(cls):
        return {
            "storage_account": StringSource,
            "container": StringSource,
            "access_key_or_sas_token": Field(Noneable(StringSource), is_required=False),
            "secret_credential": Field(
                Noneable(
                    Shape(
                        {
                            "client_id": StringSource,
                            "client_secret": StringSource,
                            "tenant_id": StringSource,
                        }
                    ),
                ),
                is_required=False,
            ),
            "default_azure_credential": Field(
                Noneable(Permissive(description="keyword arguments for DefaultAzureCredential")),
                is_required=False,
                default_value=None,
            ),
            "local_dir": Field(Noneable(StringSource), is_required=False, default_value=None),
            "prefix": Field(StringSource, is_required=False, default_value="dagster"),
            "upload_interval": Field(Noneable(int), is_required=False, default_value=None),
            "show_url_only": Field(bool, is_required=False, default_value=False),
        }

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

    def _clean_prefix(self, prefix: str) -> str:
        parts = prefix.split("/")
        return "/".join([part for part in parts if part])

    def _resolve_path_for_namespace(self, namespace: Sequence[str]) -> Sequence[str]:
        return [self._blob_prefix, "storage", *namespace]

    def _blob_key(self, log_key: Sequence[str], io_type: ComputeIOType, partial=False) -> str:
        check.inst_param(io_type, "io_type", ComputeIOType)
        extension = IO_TYPE_EXTENSION[io_type]
        [*namespace, filebase] = log_key
        filename = f"{filebase}.{extension}"
        if partial:
            filename = f"{filename}.partial"
        paths = [*self._resolve_path_for_namespace(namespace), filename]
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

    def download_url_for_type(  # pyright: ignore[reportIncompatibleMethodOverride]
        self, log_key: Sequence[str], io_type: ComputeIOType
    ) -> Optional[str]:
        if not self.is_capture_complete(log_key):
            return None

        blob_key = self._blob_key(log_key, io_type)
        if blob_key in self._download_urls:
            return self._download_urls[blob_key]
        blob = self._container_client.get_blob_client(blob_key)
        user_delegation_key = None
        account_key = None
        if hasattr(self._blob_client.credential, "account_key"):
            account_key = self._blob_client.credential.account_key
        else:
            user_delegation_key = self._request_user_delegation_key(self._blob_client)

        sas = generate_blob_sas(
            self._storage_account,
            self._container,
            blob_key,
            account_key=account_key,
            user_delegation_key=user_delegation_key,
            expiry=datetime.now() + timedelta(hours=6),
            permission=BlobSasPermissions(read=True),
        )
        url = blob.url + "?" + sas
        self._download_urls[blob_key] = url
        return url

    def _get_shell_cmd_for_type(self, log_key: Sequence[str], io_type: ComputeIOType):
        blob_key = self._blob_key(log_key, io_type)
        return f"az storage blob download --auth-mode login --account-name {self._storage_account} --container-name {self._container} --name {blob_key}"

    @contextmanager
    def capture_logs(self, log_key: Sequence[str]) -> Iterator[CapturedLogContext]:
        with super().capture_logs(log_key) as local_context:
            if not self._show_url_only:
                yield local_context
            else:
                out_key = self._blob_key(log_key, ComputeIOType.STDOUT)
                err_key = self._blob_key(log_key, ComputeIOType.STDERR)
                azure_base_url = self._container_client.url
                out_url = f"{azure_base_url}/{out_key}"
                err_url = f"{azure_base_url}/{err_key}"
                yield CapturedLogContext(
                    local_context.log_key,
                    external_stdout_url=out_url,
                    external_stderr_url=err_url,
                    shell_cmd=LogRetrievalShellCommand(
                        stdout=self._get_shell_cmd_for_type(log_key, ComputeIOType.STDOUT),
                        stderr=self._get_shell_cmd_for_type(log_key, ComputeIOType.STDERR),
                    ),
                )

    def _request_user_delegation_key(
        self,
        blob_service_client: BlobServiceClient,
    ) -> UserDelegationKey:
        """Creates user delegation key when a service principal is used or other authentication other than
        account key.
        """
        # Get a user delegation key that's valid for 1 day
        delegation_key_start_time = datetime.now(timezone.utc)
        delegation_key_expiry_time = delegation_key_start_time + timedelta(days=1)

        user_delegation_key = blob_service_client.get_user_delegation_key(
            key_start_time=delegation_key_start_time,
            key_expiry_time=delegation_key_expiry_time,
        )

        return user_delegation_key

    def display_path_for_type(self, log_key: Sequence[str], io_type: ComputeIOType) -> str:
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
            blob.upload_blob(data, **{"overwrite": partial})  # type: ignore

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

    def get_log_keys_for_log_key_prefix(
        self, log_key_prefix: Sequence[str], io_type: ComputeIOType
    ) -> Sequence[Sequence[str]]:
        directory = self._resolve_path_for_namespace(log_key_prefix)
        blobs = self._container_client.list_blobs(name_starts_with="/".join(directory))
        results = []
        list_key_prefix = list(log_key_prefix)

        for blob in blobs:
            full_key = blob.name
            filename, blob_io_type = full_key.split("/")[-1].split(".")
            if blob_io_type != IO_TYPE_EXTENSION[io_type]:
                continue
            results.append(list_key_prefix + [filename])

        return results

    def on_subscribe(self, subscription):
        self._subscription_manager.add_subscription(subscription)

    def on_unsubscribe(self, subscription):
        self._subscription_manager.remove_subscription(subscription)
