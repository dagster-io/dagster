import os
from contextlib import contextmanager

import boto3
from botocore.errorfactory import ClientError

import dagster._seven as seven
from dagster import Field, StringSource
from dagster import _check as check
from dagster._core.storage.compute_log_manager import (
    MAX_BYTES_FILE_READ,
    ComputeIOType,
    ComputeLogFileData,
    ComputeLogManager,
)
from dagster._core.storage.local_compute_log_manager import (
    IO_TYPE_EXTENSION,
    LocalComputeLogManager,
)
from dagster._serdes import ConfigurableClass, ConfigurableClassData
from dagster._utils import ensure_dir, ensure_file


class S3ComputeLogManager(ComputeLogManager, ConfigurableClass):
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
        inst_data (Optional[ConfigurableClassData]): Serializable representation of the compute
            log manager when newed up from config.
    """

    def __init__(
        self,
        bucket,
        local_dir=None,
        inst_data=None,
        prefix="dagster",
        use_ssl=True,
        verify=True,
        verify_cert_path=None,
        endpoint_url=None,
        skip_empty_files=False,
    ):
        _verify = False if not verify else verify_cert_path
        self._s3_session = boto3.resource(
            "s3", use_ssl=use_ssl, verify=_verify, endpoint_url=endpoint_url
        ).meta.client
        self._s3_bucket = check.str_param(bucket, "bucket")
        self._s3_prefix = check.str_param(prefix, "prefix")

        # proxy calls to local compute log manager (for subscriptions, etc)
        if not local_dir:
            local_dir = seven.get_system_temp_directory()

        self.local_manager = LocalComputeLogManager(local_dir)
        self._inst_data = check.opt_inst_param(inst_data, "inst_data", ConfigurableClassData)
        self._skip_empty_files = check.bool_param(skip_empty_files, "skip_empty_files")

    @contextmanager
    def _watch_logs(self, pipeline_run, step_key=None):
        # proxy watching to the local compute log manager, interacting with the filesystem
        with self.local_manager._watch_logs(  # pylint: disable=protected-access
            pipeline_run, step_key
        ):
            yield

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
        }

    @staticmethod
    def from_config_value(inst_data, config_value):
        return S3ComputeLogManager(inst_data=inst_data, **config_value)

    def get_local_path(self, run_id, key, io_type):
        return self.local_manager.get_local_path(run_id, key, io_type)

    def on_watch_start(self, pipeline_run, step_key):
        self.local_manager.on_watch_start(pipeline_run, step_key)

    def on_watch_finish(self, pipeline_run, step_key):
        self.local_manager.on_watch_finish(pipeline_run, step_key)
        key = self.local_manager.get_key(pipeline_run, step_key)
        self._upload_from_local(pipeline_run.run_id, key, ComputeIOType.STDOUT)
        self._upload_from_local(pipeline_run.run_id, key, ComputeIOType.STDERR)

    def is_watch_completed(self, run_id, key):
        return self.local_manager.is_watch_completed(run_id, key)

    def download_url(self, run_id, key, io_type):
        if not self.is_watch_completed(run_id, key):
            return self.local_manager.download_url(run_id, key, io_type)
        key = self._bucket_key(run_id, key, io_type)

        url = self._s3_session.generate_presigned_url(
            ClientMethod="get_object", Params={"Bucket": self._s3_bucket, "Key": key}
        )

        return url

    def read_logs_file(self, run_id, key, io_type, cursor=0, max_bytes=MAX_BYTES_FILE_READ):
        if self._should_download(run_id, key, io_type):
            self._download_to_local(run_id, key, io_type)
        data = self.local_manager.read_logs_file(run_id, key, io_type, cursor, max_bytes)
        return self._from_local_file_data(run_id, key, io_type, data)

    def on_subscribe(self, subscription):
        self.local_manager.on_subscribe(subscription)

    def on_unsubscribe(self, subscription):
        self.local_manager.on_unsubscribe(subscription)

    def _should_download(self, run_id, key, io_type):
        local_path = self.get_local_path(run_id, key, io_type)
        if os.path.exists(local_path):
            return False

        try:  # https://stackoverflow.com/a/38376288/14656695
            self._s3_session.head_object(
                Bucket=self._s3_bucket, Key=self._bucket_key(run_id, key, io_type)
            )
        except ClientError:
            return False

        return True

    def _from_local_file_data(self, run_id, key, io_type, local_file_data):
        is_complete = self.is_watch_completed(run_id, key)
        path = (
            "s3://{}/{}".format(self._s3_bucket, self._bucket_key(run_id, key, io_type))
            if is_complete
            else local_file_data.path
        )

        return ComputeLogFileData(
            path,
            local_file_data.data,
            local_file_data.cursor,
            local_file_data.size,
            self.download_url(run_id, key, io_type),
        )

    def _upload_from_local(self, run_id, key, io_type):
        path = self.get_local_path(run_id, key, io_type)
        ensure_file(path)
        if self._skip_empty_files and os.stat(path).st_size == 0:
            return

        key = self._bucket_key(run_id, key, io_type)
        with open(path, "rb") as data:
            self._s3_session.upload_fileobj(data, self._s3_bucket, key)

    def _download_to_local(self, run_id, key, io_type):
        path = self.get_local_path(run_id, key, io_type)
        ensure_dir(os.path.dirname(path))
        with open(path, "wb") as fileobj:
            self._s3_session.download_fileobj(
                self._s3_bucket, self._bucket_key(run_id, key, io_type), fileobj
            )

    def _bucket_key(self, run_id, key, io_type):
        check.inst_param(io_type, "io_type", ComputeIOType)
        extension = IO_TYPE_EXTENSION[io_type]
        paths = [
            self._s3_prefix,
            "storage",
            run_id,
            "compute_logs",
            "{}.{}".format(key, extension),
        ]
        return "/".join(paths)  # s3 path delimiter

    def dispose(self):
        self.local_manager.dispose()
