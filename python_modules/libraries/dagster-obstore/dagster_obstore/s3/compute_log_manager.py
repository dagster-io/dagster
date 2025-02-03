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
from obstore.store import S3Store

from dagster_obstore._base.log_manager import BaseCloudStorageComputeLogManager

if TYPE_CHECKING:
    from obstore.store import ClientConfig, S3Config

POLLING_INTERVAL = 5


class S3ComputeLogManager(BaseCloudStorageComputeLogManager, ConfigurableClass):
    """Logs compute function stdout and stderr to S3.

    Users should not instantiate this class directly. Instead, use a YAML block in ``dagster.yaml``
    such as the following:

    .. code-block:: YAML

        compute_logs:
          module: dagster_obstore.s3.compute_log_manager
          class: S3ComputeLogManager
          config:
            bucket: "mycorp-dagster-compute-logs"
            access_key_id: "access-key-id"
            secret_access_key: "my-key"
            local_dir: "/tmp/cool"
            prefix: "dagster-test-"
            allow_http: false
            allow_invalid_certificates: false
            timeout: "60s"
            endpoint: "http://alternate-s3-host.io"
            skip_empty_files: true
            upload_interval: 30
            extra_s3_args:
                aws_server_side_encryption: "AES256"
            region: "us-west-1"
            show_url_only: false


    Args:
        bucket (str): The name of the s3 bucket to which to log.
        access_key_id (Optional[str]): access key id to authenticate, if not passed it's parsed from the Environment.
        secret_access_key (Optional[str]): secret access key to authenticate, if not passed it's parsed from the Environment.
        local_dir (Optional[str]): Path to the local directory in which to stage logs. Default:
            ``dagster._seven.get_system_temp_directory()``.
        prefix (Optional[str]): Prefix for the log file keys.
        allow_http (Optional[bool]): Whether or not to allow http connections. Default False.
        allow_invalid_certificates (Optional[bool]): Whether or not to allow invalid certificates. Default False.
        timeout (str): Request timeout. Default 60s.
        endpoint (Optional[str]): Custom S3 endpoint.
        skip_empty_files: (Optional[bool]): Skip upload of empty log files.
        upload_interval: (Optional[int]): Interval in seconds to upload partial log files to S3. By default, will only upload when the capture is complete.
        extra_s3_args: (Optional[dict]): Extra args for S3 store init
        show_url_only: (Optional[bool]): Only show the URL of the log file in the UI, instead of fetching and displaying the full content. Default False.
        region: (Optional[str]): The region of the S3 bucket. If not specified, will use the default region of the AWS session.
        inst_data (Optional[ConfigurableClassData]): Serializable representation of the compute
            log manager when newed up from config.
    """

    def __init__(
        self,
        bucket: str,
        access_key_id: Optional[str] = None,
        secret_access_key: Optional[str] = None,
        local_dir: Optional[str] = None,
        inst_data: Optional[ConfigurableClassData] = None,
        prefix: Optional[str] = "dagster",
        allow_http: Optional[bool] = False,
        allow_invalid_certificates: Optional[bool] = False,
        timeout: Optional[str] = "60s",
        endpoint: Optional[str] = None,
        skip_empty_files: Optional[bool] = False,
        upload_interval: Optional[int] = None,
        extra_s3_args: Optional[dict] = None,
        show_url_only: Optional[bool] = False,
        region: Optional[str] = None,
    ):
        self._bucket = check.str_param(bucket, "bucket")
        check.opt_str_param(timeout, "timeout")
        check.opt_str_param(access_key_id, "access_key_id")
        check.opt_str_param(secret_access_key, "secret_access_key")
        self._prefix = self._clean_prefix(check.str_param(prefix, "prefix"))
        check.opt_bool_param(allow_http, "allow_http")
        check.opt_bool_param(allow_invalid_certificates, "allow_invalid_certificates")
        self._endpoint = check.opt_str_param(endpoint, "endpoint")

        # proxy calls to local compute log manager (for subscriptions, etc)
        if not local_dir:
            local_dir = seven.get_system_temp_directory()

        self._local_manager = LocalComputeLogManager(local_dir)
        self._subscription_manager = PollingComputeLogSubscriptionManager(self)
        self._inst_data = check.opt_inst_param(inst_data, "inst_data", ConfigurableClassData)
        self._skip_empty_files = check.bool_param(skip_empty_files, "skip_empty_files")
        self._upload_interval = check.opt_int_param(upload_interval, "upload_interval")
        check.opt_dict_param(extra_s3_args, "extra_s3_args")
        self._show_url_only = show_url_only
        self._region = region

        s3_config: S3Config = {}
        client_config: ClientConfig = {}
        if access_key_id:
            s3_config["access_key_id"] = access_key_id
        if secret_access_key:
            s3_config["secret_access_key"] = secret_access_key
        if endpoint:
            s3_config["endpoint"] = endpoint
        if region:
            s3_config["region"] = region

        if allow_http:
            client_config["allow_http"] = allow_http
        if allow_invalid_certificates:
            client_config["allow_invalid_certificates"] = allow_invalid_certificates
        if timeout:
            client_config["timeout"] = timeout

        self._store = S3Store.from_env(
            bucket=bucket,
            config=s3_config,
            client_options=client_config,
            **extra_s3_args if extra_s3_args is not None else {},
        )

    @classmethod
    def config_type(cls):
        return {
            "bucket": StringSource,
            "access_key_id": Field(StringSource, is_required=False),
            "secret_access_key": Field(StringSource, is_required=False),
            "local_dir": Field(StringSource, is_required=False),
            "prefix": Field(StringSource, is_required=False, default_value="dagster"),
            "allow_http": Field(bool, is_required=False, default_value=False),
            "allow_invalid_certificates": Field(bool, is_required=False, default_value=False),
            "endpoint": Field(StringSource, is_required=False),
            "timeout": Field(StringSource, is_required=False, default_value="60s"),
            "skip_empty_files": Field(bool, is_required=False, default_value=False),
            "upload_interval": Field(Noneable(int), is_required=False, default_value=None),
            "extra_s3_args": Field(
                Permissive(), is_required=False, description="Extra args for Obstore S3 init"
            ),
            "show_url_only": Field(bool, is_required=False, default_value=False),
            "region": Field(StringSource, is_required=False),
        }

    def display_path_for_type(
        self, log_key: Sequence[str], io_type: ComputeIOType
    ) -> Optional[str]:
        if not self.is_capture_complete(log_key):
            return None
        s3_key = self._blob_key(log_key, io_type)
        return f"s3://{self._bucket}/{s3_key}"
