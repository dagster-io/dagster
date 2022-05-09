import boto3
from botocore.handlers import disable_signing

import dagster._check as check

from ..utils import construct_boto_client_retry_config


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
            "Download of {bucket}/{key} to {target_path}: {percentage}% complete".format(
                bucket=self._bucket,
                key=self._key,
                target_path=self._filename,
                percentage=percentage,
            )
        )


def construct_s3_client(
    max_attempts, region_name=None, endpoint_url=None, use_unsigned_session=False, profile_name=None
):
    check.int_param(max_attempts, "max_attempts")
    check.opt_str_param(region_name, "region_name")
    check.opt_str_param(endpoint_url, "endpoint_url")
    check.bool_param(use_unsigned_session, "use_unsigned_session")
    check.opt_str_param(profile_name, "profile_name")

    client_session = boto3.session.Session(profile_name=profile_name)
    s3_client = client_session.resource(
        "s3",
        region_name=region_name,
        use_ssl=True,
        endpoint_url=endpoint_url,
        config=construct_boto_client_retry_config(max_attempts),
    ).meta.client

    if use_unsigned_session:
        s3_client.meta.events.register("choose-signer.s3.*", disable_signing)

    return s3_client
