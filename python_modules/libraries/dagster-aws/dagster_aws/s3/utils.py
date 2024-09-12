from typing import Optional, Union

import boto3
import dagster._check as check
from botocore.handlers import disable_signing

from dagster_aws.utils import construct_boto_client_retry_config


class S3Callback:
    def __init__(self, logger, bucket, key, filename, size):
        self._logger = logger
        self._bucket = bucket
        self._key = key
        self._filename = filename
        self._seen_so_far = 0
        self._size = size

    def __call__(self, bytes_amount):
        self._seen_so_far += bytes_amount
        percentage = (self._seen_so_far / self._size) * 100
        self._logger(
            f"Download of {self._bucket}/{self._key} to {self._filename}: {percentage}% complete"
        )


def construct_s3_client(
    max_attempts: int,
    region_name: Optional[str] = None,
    endpoint_url: Optional[str] = None,
    use_unsigned_session: bool = False,
    profile_name: Optional[str] = None,
    use_ssl: bool = True,
    verify: Optional[Union[str, bool]] = None,
    aws_access_key_id: Optional[str] = None,
    aws_secret_access_key: Optional[str] = None,
    aws_session_token: Optional[str] = None,
):
    check.int_param(max_attempts, "max_attempts")
    check.opt_str_param(region_name, "region_name")
    check.opt_str_param(endpoint_url, "endpoint_url")
    check.bool_param(use_unsigned_session, "use_unsigned_session")
    check.opt_str_param(profile_name, "profile_name")
    check.bool_param(use_ssl, "use_ssl")
    check.opt_str_param(profile_name, "aws_access_key_id")
    check.opt_str_param(profile_name, "aws_secret_access_key")
    check.opt_str_param(profile_name, "aws_session_token")

    client_session = boto3.session.Session(profile_name=profile_name)
    s3_client = client_session.resource(
        "s3",
        region_name=region_name,
        use_ssl=use_ssl,
        verify=verify,
        endpoint_url=endpoint_url,
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        aws_session_token=aws_session_token,
        config=construct_boto_client_retry_config(max_attempts),
    ).meta.client

    if use_unsigned_session:
        s3_client.meta.events.register("choose-signer.s3.*", disable_signing)

    return s3_client
