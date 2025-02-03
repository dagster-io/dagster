from collections.abc import Sequence
from typing import TYPE_CHECKING, Optional

import dagster._seven as seven
from dagster import (
    Field,
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
from obstore.store import GCSStore

from dagster_obstore._base.log_manager import BaseCloudStorageComputeLogManager

if TYPE_CHECKING:
    from obstore.store import ClientConfig, GCSConfig
POLLING_INTERVAL = 5


class GCSComputeLogManager(BaseCloudStorageComputeLogManager, ConfigurableClass):
    """Logs compute function stdout and stderr to GCS.

    Users should not instantiate this class directly. Instead, use a YAML block in ``dagster.yaml``
    such as the following:

    .. code-block:: YAML

        compute_logs:
          module: dagster_obstore.gcs.compute_log_manager
          class: GCSComputeLogManager
          config:
            bucket: "mycorp-dagster-compute-logs"
            service_account: "access-key-id"
            service_account_key: "my-key"
            service_account_path: "sa-path"
            local_dir: "/tmp/cool"
            prefix: "dagster-test-"
            allow_http: false
            allow_invalid_certificates: false
            timeout: "60s"
            skip_empty_files: true
            upload_interval: 30
            show_url_only: false


    Args:
        bucket (str): The name of the GCS bucket to which to log.
        service_account (Optional[str]): service account to authenticate, if not passed it's parsed from the Environment.
        service_account_key (Optional[str]): service account key to authenticate, if not passed it's parsed from the Environment.
        service_account_path (Optional[str]): path of service account key to authenticate, if not passed it's parsed from the Environment.
        local_dir (Optional[str]): Path to the local directory in which to stage logs. Default:
            ``dagster._seven.get_system_temp_directory()``.
        prefix (Optional[str]): Prefix for the log file keys.
        allow_http (Optional[bool]): Whether or not to allow http connections. Default False.
        allow_invalid_certificates (Optional[bool]): Whether or not to allow invalid certificates. Default False.
        timeout (str): Request timeout. Default 60s.
        skip_empty_files: (Optional[bool]): Skip upload of empty log files.
        upload_interval: (Optional[int]): Interval in seconds to upload partial log files to GCS. By default, will only upload when the capture is complete.
        show_url_only: (Optional[bool]): Only show the URL of the log file in the UI, instead of fetching and displaying the full content. Default False.
        inst_data (Optional[ConfigurableClassData]): Serializable representation of the compute
            log manager when newed up from config.
    """

    def __init__(
        self,
        bucket: str,
        service_account: Optional[str] = None,
        service_account_key: Optional[str] = None,
        service_account_path: Optional[str] = None,
        local_dir: Optional[str] = None,
        inst_data: Optional[ConfigurableClassData] = None,
        prefix: Optional[str] = "dagster",
        allow_http: Optional[bool] = False,
        allow_invalid_certificates: Optional[bool] = False,
        timeout: Optional[str] = "60s",
        skip_empty_files: Optional[bool] = False,
        upload_interval: Optional[int] = None,
        show_url_only: Optional[bool] = False,
    ):
        self._bucket = check.str_param(bucket, "bucket")
        check.opt_str_param(timeout, "timeout")
        check.opt_str_param(service_account, "service_account")
        check.opt_str_param(service_account_key, "service_account_key")
        check.opt_str_param(service_account_path, "service_account_path")
        self._prefix = self._clean_prefix(check.str_param(prefix, "prefix"))
        self._allow_http = check.opt_bool_param(allow_http, "allow_http")
        self._allow_invalid_certificates = check.opt_bool_param(
            allow_invalid_certificates, "allow_invalid_certificates"
        )

        # proxy calls to local compute log manager (for subscriptions, etc)
        if not local_dir:
            local_dir = seven.get_system_temp_directory()

        self._local_manager = LocalComputeLogManager(local_dir)
        self._subscription_manager = PollingComputeLogSubscriptionManager(self)
        self._inst_data = check.opt_inst_param(inst_data, "inst_data", ConfigurableClassData)
        self._skip_empty_files = check.bool_param(skip_empty_files, "skip_empty_files")
        self._upload_interval = check.opt_int_param(upload_interval, "upload_interval")
        self._show_url_only = show_url_only

        gcs_config: GCSConfig = {}
        client_config: ClientConfig = {}
        if service_account:
            gcs_config["service_account"] = service_account
        if service_account_key:
            gcs_config["service_account_key"] = service_account_key
        if service_account_path:
            gcs_config["service_account_path"] = service_account_path

        if allow_http:
            client_config["allow_http"] = allow_http
        if allow_invalid_certificates:
            client_config["allow_invalid_certificates"] = allow_invalid_certificates
        if timeout:
            client_config["timeout"] = timeout

        self._store = GCSStore.from_env(
            bucket=bucket,
            config=gcs_config,
            client_options=client_config,
        )

    @classmethod
    def config_type(cls):
        return {
            "bucket": StringSource,
            "service_account": Field(StringSource, is_required=False),
            "service_account_key": Field(StringSource, is_required=False),
            "service_account_path": Field(StringSource, is_required=False),
            "local_dir": Field(StringSource, is_required=False),
            "prefix": Field(StringSource, is_required=False, default_value="dagster"),
            "allow_http": Field(bool, is_required=False, default_value=False),
            "allow_invalid_certificates": Field(bool, is_required=False, default_value=False),
            "timeout": Field(StringSource, is_required=False, default_value="60s"),
            "skip_empty_files": Field(bool, is_required=False, default_value=False),
            "upload_interval": Field(Noneable(int), is_required=False, default_value=None),
            "show_url_only": Field(bool, is_required=False, default_value=False),
        }

    def display_path_for_type(
        self, log_key: Sequence[str], io_type: ComputeIOType
    ) -> Optional[str]:
        if not self.is_capture_complete(log_key):
            return None
        blob_key = self._blob_key(log_key, io_type)
        return f"gcs://{self._bucket}/{blob_key}"
