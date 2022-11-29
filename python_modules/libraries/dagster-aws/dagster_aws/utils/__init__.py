from botocore import __version__ as botocore_version
from botocore.config import Config
from packaging import version

import dagster._check as check
from dagster import Field


def construct_boto_client_retry_config(max_attempts):
    check.int_param(max_attempts, "max_attempts")

    # retry mode option was introduced in botocore 1.15.0
    # https://botocore.amazonaws.com/v1/documentation/api/1.15.0/reference/config.html
    retry_config = {"max_attempts": max_attempts}
    if version.parse(botocore_version) >= version.parse("1.15.0"):
        retry_config["mode"] = "standard"
    return Config(retries=retry_config)


BOTO3_SESSION_CONFIG = {
    "region_name": Field(
        str,
        description="Specifies a custom region for the Boto3 session",
        is_required=False,
    ),
    "max_attempts": Field(
        int,
        description="This provides Boto3's retry handler with a value of maximum retry attempts, "
        "where the initial call counts toward the max_attempts value that you provide",
        is_required=False,
        default_value=5,
    ),
    "profile_name": Field(
        str,
        description="Specifies a profile to connect that session",
        is_required=False,
    ),
}
