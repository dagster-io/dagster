"""Tests for the ``dagster-aws/<version>`` product token and the optional
``user_agent_extra`` knob on ``S3Resource`` / ``S3FileManagerResource``.

Every boto3 S3 client constructed via these resources carries
``dagster-aws/<version>`` in its ``user_agent_extra``, and works against Amazon
S3 as well as any S3-compatible object store. Any caller-supplied
``user_agent_extra`` is appended after the product token with a space
separator, and never replaces it.
"""

from importlib.metadata import PackageNotFoundError, version

from dagster_aws.s3 import S3Resource
from dagster_aws.s3.resources import S3FileManagerResource
from dagster_aws.s3.utils import construct_s3_client

try:
    DAGSTER_AWS_PRODUCT = f"dagster-aws/{version('dagster-aws')}"
except PackageNotFoundError:
    DAGSTER_AWS_PRODUCT = "dagster-aws/dev"


def test_construct_s3_client_default_carries_product_token() -> None:
    """With no caller-supplied extra, only ``dagster-aws/<version>`` is appended."""
    client = construct_s3_client(max_attempts=5)
    extra = client.meta.config.user_agent_extra or ""
    assert extra.strip() == DAGSTER_AWS_PRODUCT
    # The base SDK token is preserved, not replaced.
    assert "Boto3/" in client.meta.config.user_agent
    assert DAGSTER_AWS_PRODUCT in client.meta.config.user_agent


def test_construct_s3_client_appends_user_agent_extra_after_product_token() -> None:
    """Caller-supplied tokens are appended after the product token, not in place of it."""
    caller_token = "my-platform/1.2.3"
    client = construct_s3_client(max_attempts=5, user_agent_extra=caller_token)
    extra = client.meta.config.user_agent_extra or ""
    assert DAGSTER_AWS_PRODUCT in extra
    assert caller_token in extra
    # Order: product token first, caller token after, space-separated.
    assert extra == f"{DAGSTER_AWS_PRODUCT} {caller_token}"
    assert "Boto3/" in client.meta.config.user_agent
    assert caller_token in client.meta.config.user_agent


def test_construct_s3_client_empty_user_agent_extra_treated_as_unset() -> None:
    """An empty string should not change behavior: only the product token is appended."""
    client = construct_s3_client(max_attempts=5, user_agent_extra="")
    extra = client.meta.config.user_agent_extra or ""
    assert extra.strip() == DAGSTER_AWS_PRODUCT


def test_construct_s3_client_preserves_retry_config() -> None:
    """Merging the product token must not drop the retry config already in the chain."""
    client = construct_s3_client(max_attempts=7, user_agent_extra="my-platform/1.2.3")
    retries = client.meta.config.retries
    # botocore records the initial call plus retries as ``total_max_attempts``.
    assert retries["total_max_attempts"] == 8
    assert retries["mode"] == "standard"
    extra = client.meta.config.user_agent_extra or ""
    assert DAGSTER_AWS_PRODUCT in extra
    assert "my-platform/1.2.3" in extra


def test_s3_resource_default_carries_product_token() -> None:
    client = S3Resource().get_client()
    extra = client.meta.config.user_agent_extra or ""
    assert extra.strip() == DAGSTER_AWS_PRODUCT


def test_s3_resource_threads_user_agent_extra_to_client() -> None:
    client = S3Resource(user_agent_extra="my-platform/1.2.3").get_client()
    extra = client.meta.config.user_agent_extra or ""
    assert extra == f"{DAGSTER_AWS_PRODUCT} my-platform/1.2.3"


def test_s3_resource_user_agent_extra_with_custom_endpoint() -> None:
    """End-to-end shape a user of an S3-compatible object store would write."""
    resource = S3Resource(
        endpoint_url="https://your-s3-endpoint.example.com",
        aws_access_key_id="<your-access-key-id>",
        aws_secret_access_key="<your-secret-access-key>",
        user_agent_extra="my-platform/1.2.3",
    )
    client = resource.get_client()
    assert client.meta.endpoint_url == "https://your-s3-endpoint.example.com"
    extra = client.meta.config.user_agent_extra or ""
    assert DAGSTER_AWS_PRODUCT in extra
    assert "my-platform/1.2.3" in extra


def test_s3_file_manager_resource_threads_user_agent_extra() -> None:
    file_manager = S3FileManagerResource(
        s3_bucket="my-bucket",
        user_agent_extra="my-platform/1.2.3",
    ).get_client()
    # ``S3FileManager`` stores the wrapped boto3 client as ``_s3_session``.
    extra = file_manager._s3_session.meta.config.user_agent_extra or ""  # noqa: SLF001
    assert extra == f"{DAGSTER_AWS_PRODUCT} my-platform/1.2.3"


def test_s3_file_manager_resource_default_carries_product_token() -> None:
    file_manager = S3FileManagerResource(s3_bucket="my-bucket").get_client()
    extra = file_manager._s3_session.meta.config.user_agent_extra or ""  # noqa: SLF001
    assert extra.strip() == DAGSTER_AWS_PRODUCT
