import datetime
import io
import os
import pickle
from typing import Any

import boto3
import dagster._check as check
import requests
from dagster import InputContext, OutputContext, UPathIOManager, io_manager
from dagster._utils import PICKLE_PROTOCOL
from dagster._vendored.dateutil import parser
from dagster_cloud_cli.core.headers.auth import DagsterCloudInstanceScope
from dagster_cloud_cli.core.headers.impl import get_dagster_cloud_api_headers
from upath import UPath

ECS_AGENT_IP = "169.254.170.2"


class PickledObjectServerlessIOManager(UPathIOManager):
    def __init__(
        self,
        s3_bucket,
        s3_prefix,
    ):
        self._bucket = check.str_param(s3_bucket, "s3_bucket")
        self._s3_prefix = check.str_param(s3_prefix, "s3_prefix")
        self._boto_session, self._boto_session_expiration = self._refresh_boto_session()
        base_path = UPath(s3_prefix) if s3_prefix else None
        super().__init__(base_path=base_path)

    def _refresh_boto_session(self) -> tuple[boto3.Session, datetime.datetime]:
        # We have to do this whacky way to get credentials to ensure that we get iam role
        # we assigned to the task. If we used the default boto behavior, it could get overriden
        # when users set AWS env vars.
        relative_uri = os.environ["AWS_CONTAINER_CREDENTIALS_RELATIVE_URI"]
        aws_creds = requests.get(f"http://{ECS_AGENT_IP}{relative_uri}").json()
        session = boto3.Session(
            aws_access_key_id=aws_creds["AccessKeyId"],
            aws_secret_access_key=aws_creds["SecretAccessKey"],
            aws_session_token=aws_creds["Token"],
        )
        expiration = parser.parse(aws_creds["Expiration"])
        return session, expiration

    @property
    def _s3(self):
        if self._boto_session_expiration <= datetime.datetime.now(
            self._boto_session_expiration.tzinfo
        ) + datetime.timedelta(minutes=5):
            self._boto_session, self._boto_session_expiration = self._refresh_boto_session()
        return self._boto_session.client(
            "s3",
            region_name=os.getenv("DAGSTER_CLOUD_SERVERLESS_REGION", "us-west-2"),
        )

    def load_from_path(self, context: InputContext, path: UPath) -> Any:
        try:
            s3_obj = self._s3.get_object(Bucket=self._bucket, Key=path.as_posix())["Body"].read()
            return pickle.loads(s3_obj)
        except self._s3.exceptions.NoSuchKey:
            raise FileNotFoundError(
                f"Could not find the input for '{context.name}'. It may have expired."
            )

    def dump_to_path(self, context: OutputContext, obj: Any, path: UPath) -> None:
        pickled_obj = pickle.dumps(obj, PICKLE_PROTOCOL)
        pickled_obj_bytes = io.BytesIO(pickled_obj)
        self._s3.upload_fileobj(pickled_obj_bytes, self._bucket, path.as_posix())

    def path_exists(self, path: UPath) -> bool:
        try:
            self._s3.get_object(Bucket=self._bucket, Key=path.as_posix())
        except self._s3.exceptions.NoSuchKey:
            return False
        return True

    def unlink(self, path: UPath) -> None:
        self._s3.delete_object(Bucket=self._bucket, Key=path.as_posix())

    def make_directory(self, path: UPath) -> None:
        # It is not necessary to create directories in S3
        return None

    def get_op_output_relative_path(self, context: InputContext | OutputContext):
        from upath import UPath

        return UPath(*["storage", *context.get_identifier()])


class ServerlessPresignedURLIOManager(UPathIOManager):
    """IO manager for Dagster+ that stores artifacts via the Dagster+ API.

    No AWS credentials required in user pods. Presigned PUT/GET URLs are
    obtained from the Dagster+ API on each operation.
    """

    def __init__(self, api_url: str, api_token: str, timeout: int):
        self._api_url = api_url
        self._api_token = api_token
        self._timeout = timeout
        self._session = requests.Session()
        super().__init__(base_path=UPath("."))

    def _get_presigned_url(self, key: str, method: str) -> str:
        resp = self._session.get(
            f"{self._api_url}/gen_io_storage_url",
            headers=get_dagster_cloud_api_headers(
                self._api_token,
                DagsterCloudInstanceScope.DEPLOYMENT,
            ),
            params={"key": key, "method": method},
            timeout=self._timeout,
        )
        resp.raise_for_status()
        return resp.json()["url"]

    def load_from_path(self, context: InputContext, path: UPath) -> Any:
        key = path.as_posix()
        url = self._get_presigned_url(key, "GET")
        resp = self._session.get(url, timeout=self._timeout)
        if resp.status_code == 404:
            raise FileNotFoundError(
                f"Could not find the input for '{context.name}'."
                " The upstream output may not have been materialized yet."
            )
        resp.raise_for_status()
        return pickle.loads(resp.content)

    def dump_to_path(self, context: OutputContext, obj: Any, path: UPath) -> None:
        key = path.as_posix()
        url = self._get_presigned_url(key, "PUT")
        pickled = pickle.dumps(obj, PICKLE_PROTOCOL)
        resp = self._session.put(url, data=pickled, timeout=self._timeout)
        resp.raise_for_status()

    def path_exists(self, path: UPath) -> bool:
        key = path.as_posix()
        url = self._get_presigned_url(key, "HEAD")
        resp = self._session.head(url, timeout=self._timeout)
        return resp.status_code == 200

    def unlink(self, path: UPath) -> None:
        key = path.as_posix()
        url = self._get_presigned_url(key, "DELETE")
        resp = self._session.delete(url, timeout=self._timeout)
        resp.raise_for_status()

    def make_directory(self, path: UPath) -> None:
        pass

    def get_op_output_relative_path(self, context: InputContext | OutputContext) -> UPath:
        return UPath(*["storage", *context.get_identifier()])


def _build_serverless_io_manager(init_context):
    if os.getenv("SERVERLESS_IO_MANAGER_USE_PRESIGNED_URL"):
        return ServerlessPresignedURLIOManager(
            api_url=init_context.instance.dagster_cloud_url,
            api_token=init_context.instance.dagster_cloud_agent_token,
            timeout=init_context.instance.dagster_cloud_api_timeout,
        )

    bucket = os.getenv("DAGSTER_CLOUD_SERVERLESS_STORAGE_S3_BUCKET")
    prefix = os.getenv("DAGSTER_CLOUD_SERVERLESS_STORAGE_S3_PREFIX")
    check.invariant(
        bucket and prefix,
        "The serverless_io_manager is only supported when running on Dagster Cloud Serverless."
        " DAGSTER_CLOUD_SERVERLESS_STORAGE_S3_BUCKET or"
        " DAGSTER_CLOUD_SERVERLESS_STORAGE_S3_PREFIX not found.",
    )

    deployment_name = init_context.instance.deployment_name

    return PickledObjectServerlessIOManager(
        bucket, s3_prefix=f"{prefix}/io_storage/{deployment_name}"
    )


@io_manager
def serverless_io_manager(init_context):
    return _build_serverless_io_manager(init_context)
