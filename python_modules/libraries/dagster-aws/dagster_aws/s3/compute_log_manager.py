import os
from contextlib import contextmanager
from typing import Any, Iterator, Mapping, Optional, Sequence

import boto3
import dagster._seven as seven
from botocore.errorfactory import ClientError
from dagster import (
    Field,
    Permissive,
    StringSource,
    _check as check,
)
from dagster._config.config_type import Noneable
from dagster._core.storage.captured_log_manager import CapturedLogContext
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

POLLING_INTERVAL = 5


class S3ComputeLogManager(CloudStorageComputeLogManager, ConfigurableClass):
    """Logs compute function stdout and stderr to S3.

    Users should not instantiate this class directly. Instead, use a YAML block in ``dagster.yaml``
    such as the following:

    .. code-block:: YAML

        compute_logs:
          module: dagster_aws.s3.compute_log_manager
          class: S3ComputeLogManager
          config:
            bucket: "mycorp-dagster-compute-logs"
            local_dir: "/tmp/cool"
            prefix: "dagster-test-"
            use_ssl: true
            verify: true
            verify_cert_path: "/path/to/cert/bundle.pem"
            endpoint_url: "http://alternate-s3-host.io"
            skip_empty_files: true
            upload_interval: 30
            upload_extra_args:
              ServerSideEncryption: "AES256"
            show_url_only: false
            region: "us-west-1"

    Args:
        bucket (str): The name of the s3 bucket to which to log.
        local_dir (Optional[str]): Path to the local directory in which to stage logs. Default:
            ``dagster._seven.get_system_temp_directory()``.
        prefix (Optional[str]): Prefix for the log file keys.
        use_ssl (Optional[bool]): Whether or not to use SSL. Default True.
        verify (Optional[bool]): Whether or not to verify SSL certificates. Default True.
        verify_cert_path (Optional[str]): A filename of the CA cert bundle to use. Only used if
            `verify` set to False.
        endpoint_url (Optional[str]): Override for the S3 endpoint url.
        skip_empty_files: (Optional[bool]): Skip upload of empty log files.
        upload_interval: (Optional[int]): Interval in seconds to upload partial log files to S3. By default, will only upload when the capture is complete.
        upload_extra_args: (Optional[dict]): Extra args for S3 file upload
        show_url_only: (Optional[bool]): Only show the URL of the log file in the UI, instead of fetching and displaying the full content. Default False.
        region: (Optional[str]): The region of the S3 bucket. If not specified, will use the default region of the AWS session.
        inst_data (Optional[ConfigurableClassData]): Serializable representation of the compute
            log manager when newed up from config.
    """

    def __init__(
        self,
        bucket,
        local_dir=None,
        inst_data: Optional[ConfigurableClassData] = None,
        prefix="dagster",
        use_ssl=True,
        verify=True,
        verify_cert_path=None,
        endpoint_url=None,
        skip_empty_files=False,
        upload_interval=None,
        upload_extra_args=None,
        show_url_only=False,
        region=None,
    ):
        _verify = False if not verify else verify_cert_path
        self._s3_session = boto3.resource(
            "s3", use_ssl=use_ssl, verify=_verify, endpoint_url=endpoint_url
        ).meta.client
        self._s3_bucket = check.str_param(bucket, "bucket")
        self._s3_prefix = self._clean_prefix(check.str_param(prefix, "prefix"))

        # proxy calls to local compute log manager (for subscriptions, etc)
        if not local_dir:
            local_dir = seven.get_system_temp_directory()

        self._local_manager = LocalComputeLogManager(local_dir)
        self._subscription_manager = PollingComputeLogSubscriptionManager(self)
        self._inst_data = check.opt_inst_param(inst_data, "inst_data", ConfigurableClassData)
        self._skip_empty_files = check.bool_param(skip_empty_files, "skip_empty_files")
        self._upload_interval = check.opt_int_param(upload_interval, "upload_interval")
        check.opt_dict_param(upload_extra_args, "upload_extra_args")
        self._upload_extra_args = upload_extra_args
        self._show_url_only = show_url_only
        if region is None:
            # if unspecified, use the current session name
            self._region = self._s3_session.meta.region_name
        else:
            self._region = region

    @property
    def inst_data(self):
        return self._inst_data

    @classmethod
    def config_type(cls):
        return {
            "bucket": StringSource,
            "local_dir": Field(StringSource, is_required=False),
            "prefix": Field(StringSource, is_required=False, default_value="dagster"),
            "use_ssl": Field(bool, is_required=False, default_value=True),
            "verify": Field(bool, is_required=False, default_value=True),
            "verify_cert_path": Field(StringSource, is_required=False),
            "endpoint_url": Field(StringSource, is_required=False),
            "skip_empty_files": Field(bool, is_required=False, default_value=False),
            "upload_interval": Field(Noneable(int), is_required=False, default_value=None),
            "upload_extra_args": Field(
                Permissive(), is_required=False, description="Extra args for S3 file upload"
            ),
            "show_url_only": Field(bool, is_required=False, default_value=False),
            "region": Field(StringSource, is_required=False),
        }

    @classmethod
    def from_config_value(
        cls, inst_data: ConfigurableClassData, config_value: Mapping[str, Any]
    ) -> Self:
        return S3ComputeLogManager(inst_data=inst_data, **config_value)

    @property
    def local_manager(self) -> LocalComputeLogManager:
        return self._local_manager

    @property
    def upload_interval(self) -> Optional[int]:
        return self._upload_interval if self._upload_interval else None

    def _clean_prefix(self, prefix):
        parts = prefix.split("/")
        return "/".join([part for part in parts if part])

    def _s3_key(self, log_key, io_type, partial=False):
        check.inst_param(io_type, "io_type", ComputeIOType)
        extension = IO_TYPE_EXTENSION[io_type]
        [*namespace, filebase] = log_key
        filename = f"{filebase}.{extension}"
        if partial:
            filename = f"{filename}.partial"
        paths = [self._s3_prefix, "storage", *namespace, filename]
        return "/".join(paths)  # s3 path delimiter

    @contextmanager
    def capture_logs(self, log_key: Sequence[str]) -> Iterator[CapturedLogContext]:
        with super().capture_logs(log_key) as local_context:
            if not self._show_url_only:
                yield local_context
            else:
                out_key = self._s3_key(log_key, ComputeIOType.STDOUT)
                err_key = self._s3_key(log_key, ComputeIOType.STDERR)
                s3_base = f"https://s3.console.aws.amazon.com/s3/object/{self._s3_bucket}?region={self._region}"
                yield CapturedLogContext(
                    local_context.log_key,
                    external_stdout_url=f"{s3_base}&prefix={out_key}",
                    external_stderr_url=f"{s3_base}&prefix={err_key}",
                )

    def delete_logs(
        self, log_key: Optional[Sequence[str]] = None, prefix: Optional[Sequence[str]] = None
    ):
        self.local_manager.delete_logs(log_key=log_key, prefix=prefix)

        s3_keys_to_remove = None
        if log_key:
            s3_keys_to_remove = [
                self._s3_key(log_key, ComputeIOType.STDOUT),
                self._s3_key(log_key, ComputeIOType.STDERR),
                self._s3_key(log_key, ComputeIOType.STDOUT, partial=True),
                self._s3_key(log_key, ComputeIOType.STDERR, partial=True),
            ]
        elif prefix:
            # add the trailing '' to make sure that ['a'] does not match ['apple']
            s3_prefix = "/".join([self._s3_prefix, "storage", *prefix, ""])
            matching = self._s3_session.list_objects(Bucket=self._s3_bucket, Prefix=s3_prefix)
            s3_keys_to_remove = [obj["Key"] for obj in matching.get("Contents", [])]
        else:
            check.failed("Must pass in either `log_key` or `prefix` argument to delete_logs")

        if s3_keys_to_remove:
            to_delete = [{"Key": key} for key in s3_keys_to_remove]
            self._s3_session.delete_objects(Bucket=self._s3_bucket, Delete={"Objects": to_delete})

    def download_url_for_type(self, log_key: Sequence[str], io_type: ComputeIOType):
        if not self.is_capture_complete(log_key):
            return None

        s3_key = self._s3_key(log_key, io_type)
        return self._s3_session.generate_presigned_url(
            ClientMethod="get_object", Params={"Bucket": self._s3_bucket, "Key": s3_key}
        )

    def display_path_for_type(self, log_key: Sequence[str], io_type: ComputeIOType):
        if not self.is_capture_complete(log_key):
            return None
        s3_key = self._s3_key(log_key, io_type)
        return f"s3://{self._s3_bucket}/{s3_key}"

    def cloud_storage_has_logs(
        self, log_key: Sequence[str], io_type: ComputeIOType, partial: bool = False
    ) -> bool:
        s3_key = self._s3_key(log_key, io_type, partial=partial)
        try:  # https://stackoverflow.com/a/38376288/14656695
            self._s3_session.head_object(Bucket=self._s3_bucket, Key=s3_key)
        except ClientError:
            return False
        return True

    def upload_to_cloud_storage(
        self, log_key: Sequence[str], io_type: ComputeIOType, partial=False
    ):
        path = self.local_manager.get_captured_local_path(log_key, IO_TYPE_EXTENSION[io_type])
        ensure_file(path)

        if (self._skip_empty_files or partial) and os.stat(path).st_size == 0:
            return

        s3_key = self._s3_key(log_key, io_type, partial=partial)
        with open(path, "rb") as data:
            extra_args = {
                "ContentType": "text/plain",
                **(self._upload_extra_args if self._upload_extra_args else {}),
            }
            self._s3_session.upload_fileobj(data, self._s3_bucket, s3_key, ExtraArgs=extra_args)

    def download_from_cloud_storage(
        self, log_key: Sequence[str], io_type: ComputeIOType, partial=False
    ):
        path = self._local_manager.get_captured_local_path(
            log_key, IO_TYPE_EXTENSION[io_type], partial=partial
        )
        ensure_dir(os.path.dirname(path))
        s3_key = self._s3_key(log_key, io_type, partial=partial)
        with open(path, "wb") as fileobj:
            self._s3_session.download_fileobj(self._s3_bucket, s3_key, fileobj)

    def on_subscribe(self, subscription):
        self._subscription_manager.add_subscription(subscription)

    def on_unsubscribe(self, subscription):
        self._subscription_manager.remove_subscription(subscription)

    def dispose(self):
        self._subscription_manager.dispose()
        self._local_manager.dispose()
