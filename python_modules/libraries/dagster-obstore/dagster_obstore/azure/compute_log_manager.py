from collections.abc import Sequence
from typing import TYPE_CHECKING, Optional

import dagster._seven as seven
from dagster import (
    Field,
    Permissive,
    StringSource,
    _check as check,
)
from dagster._config.config_type import Noneable
from dagster._core.storage.cloud_storage_compute_log_manager import (
    PollingComputeLogSubscriptionManager,
)
from dagster._core.storage.compute_log_manager import ComputeIOType
from dagster._core.storage.local_compute_log_manager import LocalComputeLogManager
from dagster._serdes import ConfigurableClass, ConfigurableClassData
from obstore.store import AzureStore

from dagster_obstore._base.log_manager import BaseCloudStorageComputeLogManager

POLLING_INTERVAL = 5


if TYPE_CHECKING:
    from obstore.store import AzureConfig, ClientConfig


class ADLSComputeLogManager(BaseCloudStorageComputeLogManager, ConfigurableClass):
    """Logs compute function stdout and stderr to ADLS.

    Users should not instantiate this class directly. Instead, use a YAML block in ``dagster.yaml``
    such as the following:

    .. code-block:: YAML

        compute_logs:
          module: dagster_obstore.azure.compute_log_manager
          class: ADLSComputeLogManager
          config:
            storage_account: "storage-account"
            container: "mycorp-dagster-compute-logs"
            access_key: "my-key"
            local_dir: "/tmp/cool"
            prefix: "dagster-test-"
            allow_http: false
            allow_invalid_certificates: false
            timeout: "60s"
            skip_empty_files: true
            upload_interval: 30
            extra_azure_args:
                azure_identity_endpoint: "http://custom-endpoint"
            show_url_only: false

    .. code-block:: YAML

        compute_logs:
          module: dagster_obstore.azure.compute_log_manager
          class: ADLSComputeLogManager
          config:
            storage_account: "storage-account"
            container: "mycorp-dagster-compute-logs"
            client_id: "my-client-id"
            client_secret: "my-client-secret"
            tenant_id: "id-of-azure-tenant"
            local_dir: "/tmp/cool"
            prefix: "dagster-test-"
            allow_http: false
            allow_invalid_certificates: false
            timeout: "60s"
            skip_empty_files: true
            upload_interval: 30
            extra_azure_args:
                azure_identity_endpoint: "http://custom-endpoint"
            show_url_only: false

    Args:
        storage_account (str): The storage account name to which to log.
        container (str): The name of the ADLS/blob container to which to log.
        client_id (Optional[str]):
        client_secret (Optional[str]):
        tenant_id (Optional[str]):
        sas_token (Optional[str]):
        access_key (Optional[str]):
        use_azure_cli (Optional[bool]):
        local_dir (Optional[str]): Path to the local directory in which to stage logs. Default:
            ``dagster._seven.get_system_temp_directory()``.
        prefix (Optional[str]): Prefix for the log file keys.
        allow_http (Optional[bool]): Whether or not to allow http connections. Default False.
        allow_invalid_certificates (Optional[bool]): Whether or not to allow invalid certificates. Default False.
        timeout (str): Request timeout. Default 60s.
        skip_empty_files: (Optional[bool]): Skip upload of empty log files.
        upload_interval: (Optional[int]): Interval in seconds to upload partial log files to ADLS. By default, will only upload when the capture is complete.
        extra_azure_args: (Optional[dict]): Extra args for Azure store init
        show_url_only: (Optional[bool]): Only show the URL of the log file in the UI, instead of fetching and displaying the full content. Default False.
        inst_data (Optional[ConfigurableClassData]): Serializable representation of the compute
            log manager when newed up from config.
    """

    def __init__(
        self,
        storage_account: str,
        container: str,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        tenant_id: Optional[str] = None,
        sas_token: Optional[str] = None,
        access_key: Optional[str] = None,
        use_azure_cli: Optional[bool] = None,
        local_dir: Optional[str] = None,
        inst_data: Optional[ConfigurableClassData] = None,
        prefix: Optional[str] = "dagster",
        allow_http: Optional[bool] = False,
        allow_invalid_certificates: Optional[bool] = False,
        timeout: Optional[str] = "60s",
        skip_empty_files: Optional[bool] = False,
        upload_interval: Optional[int] = None,
        extra_azure_args: Optional[dict] = None,
        show_url_only: Optional[bool] = False,
    ):
        self._storage_account = check.str_param(storage_account, "storage_account")
        self._container = check.str_param(container, "container")
        self._prefix = self._clean_prefix(check.str_param(prefix, "prefix"))
        check.opt_str_param(client_id, "client_id")
        check.opt_str_param(client_secret, "client_secret")
        check.opt_str_param(tenant_id, "tenant_id")
        check.opt_str_param(client_id, "client_id")
        check.opt_str_param(sas_token, "sas_token")
        check.opt_str_param(access_key, "access_key")
        check.opt_bool_param(use_azure_cli, "use_azure_cli")

        check.opt_str_param(timeout, "timeout")
        check.opt_bool_param(allow_http, "allow_http")
        check.opt_bool_param(allow_invalid_certificates, "allow_invalid_certificates")

        # proxy calls to local compute log manager (for subscriptions, etc)
        if not local_dir:
            local_dir = seven.get_system_temp_directory()

        self._local_manager = LocalComputeLogManager(local_dir)
        self._subscription_manager = PollingComputeLogSubscriptionManager(self)
        self._inst_data = check.opt_inst_param(inst_data, "inst_data", ConfigurableClassData)
        self._skip_empty_files = check.bool_param(skip_empty_files, "skip_empty_files")
        self._upload_interval = check.opt_int_param(upload_interval, "upload_interval")
        self._show_url_only = show_url_only

        azure_config: AzureConfig = {}
        client_config: ClientConfig = {}

        if storage_account:
            azure_config["azure_storage_account_name"] = storage_account

        if client_id:
            azure_config["client_id"] = client_id
        if client_secret:
            azure_config["client_secret"] = client_secret
        if tenant_id:
            azure_config["tenant_id"] = tenant_id

        if sas_token:
            azure_config["sas_token"] = sas_token

        if access_key:
            azure_config["access_key"] = access_key

        if use_azure_cli:
            azure_config["use_azure_cli"] = use_azure_cli

        if allow_http:
            client_config["allow_http"] = allow_http
        if allow_invalid_certificates:
            client_config["allow_invalid_certificates"] = allow_invalid_certificates
        if timeout:
            client_config["timeout"] = timeout

        self._store = AzureStore.from_env(
            container=container,
            config=azure_config,
            client_options=client_config,
            **extra_azure_args if extra_azure_args is not None else {},
        )

    @classmethod
    def config_type(cls):
        return {
            "storage_account": StringSource,
            "container": StringSource,
            "client_id": Field(StringSource, is_required=False),
            "client_secret": Field(StringSource, is_required=False),
            "tenant_id": Field(StringSource, is_required=False),
            "sas_token": Field(StringSource, is_required=False),
            "access_key": Field(StringSource, is_required=False),
            "use_azure_cli": Field(bool, is_required=False),
            "local_dir": Field(StringSource, is_required=False),
            "prefix": Field(StringSource, is_required=False, default_value="dagster"),
            "allow_http": Field(bool, is_required=False, default_value=False),
            "allow_invalid_certificates": Field(bool, is_required=False, default_value=False),
            "timeout": Field(StringSource, is_required=False, default_value="60s"),
            "skip_empty_files": Field(bool, is_required=False, default_value=False),
            "upload_interval": Field(Noneable(int), is_required=False, default_value=None),
            "extra_azure_args": Field(
                Permissive(), is_required=False, description="Extra args for Obstore Azure init"
            ),
            "show_url_only": Field(bool, is_required=False, default_value=False),
        }

    def display_path_for_type(
        self, log_key: Sequence[str], io_type: ComputeIOType
    ) -> Optional[str]:
        if not self.is_capture_complete(log_key):
            return None
        blob_key = self._blob_key(log_key, io_type)
        return f"https://{self._storage_account}.blob.core.windows.net/{self._container}/{blob_key}"
