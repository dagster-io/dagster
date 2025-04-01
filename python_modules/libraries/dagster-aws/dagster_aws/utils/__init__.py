import sys
from pathlib import Path
from typing import Optional, TypeVar

import dagster._check as check
from botocore import __version__ as botocore_version
from botocore.config import Config
from dagster import ConfigurableResource
from packaging import version
from pydantic import Field

from dagster_aws import __file__ as dagster_aws_init_py


def construct_boto_client_retry_config(max_attempts):
    check.int_param(max_attempts, "max_attempts")

    # retry mode option was introduced in botocore 1.15.0
    # https://botocore.amazonaws.com/v1/documentation/api/1.15.0/reference/config.html
    retry_config = {"max_attempts": max_attempts}
    if version.parse(botocore_version) >= version.parse("1.15.0"):
        retry_config["mode"] = "standard"
    return Config(retries=retry_config)  # pyright: ignore[reportArgumentType]


T = TypeVar("T")


class ResourceWithBoto3Configuration(ConfigurableResource):
    region_name: Optional[str] = Field(
        default=None, description="Specifies a custom region for the Boto3 session"
    )
    max_attempts: int = Field(
        default=5,
        description=(
            "This provides Boto3's retry handler with a value of maximum retry attempts, where the"
            " initial call counts toward the max_attempts value that you provide"
        ),
    )
    profile_name: Optional[str] = Field(
        default=None, description="Specifies a profile to connect that session"
    )
    use_ssl: bool = Field(
        default=True, description="Whether or not to use SSL. By default, SSL is used."
    )
    endpoint_url: Optional[str] = Field(
        default=None, description="Specifies a custom endpoint for the Boto3 session."
    )
    verify: Optional[bool] = Field(
        default=True,
        description=(
            "Whether or not to verify SSL certificates. By default SSL certificates are verified."
        ),
    )
    aws_access_key_id: Optional[str] = Field(
        default=None, description="AWS access key ID to use when creating the boto3 session."
    )
    aws_secret_access_key: Optional[str] = Field(
        default=None, description="AWS secret access key to use when creating the boto3 session."
    )
    aws_session_token: Optional[str] = Field(
        default=None, description="AWS session token to use when creating the boto3 session."
    )


def ensure_dagster_aws_tests_import() -> None:
    dagster_package_root = (Path(dagster_aws_init_py) / ".." / "..").resolve()
    assert (
        dagster_package_root / "dagster_aws_tests"
    ).exists(), "Could not find dagster_aws_tests where expected"
    sys.path.append(dagster_package_root.as_posix())
