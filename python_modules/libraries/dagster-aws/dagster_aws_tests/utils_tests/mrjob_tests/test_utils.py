import ssl
import time
from datetime import datetime, timedelta

import botocore
from dagster._vendored.dateutil.tz import tzutc

from dagster_aws.utils.mrjob.utils import (
    _boto3_now,
    _client_error_code,
    _client_error_status,
    _is_retriable_client_error,
    _wrap_aws_client,
    strip_microseconds,
)

EPS = 10.0


def test_client_error_code():
    code = "Timeout"
    ex = botocore.exceptions.ClientError({"Error": {"Code": code}}, "foo")  # pyright: ignore[reportAttributeAccessIssue]
    assert _client_error_code(ex) == code

    empty_ex = botocore.exceptions.ClientError({}, "foo")  # pyright: ignore[reportAttributeAccessIssue]
    assert _client_error_code(empty_ex) == ""


def test_client_error_status():
    code = 403
    ex = botocore.exceptions.ClientError({"Error": {"HTTPStatusCode": code}}, "foo")  # pyright: ignore[reportAttributeAccessIssue]
    assert _client_error_status(ex) == code

    empty_ex = botocore.exceptions.ClientError({}, "foo")  # pyright: ignore[reportAttributeAccessIssue]
    assert _client_error_status(empty_ex) is None


def test_is_retriable_client_error():
    ex = botocore.exceptions.ClientError({"Error": {"Code": "Timeout"}}, "foo")  # pyright: ignore[reportAttributeAccessIssue]
    assert _is_retriable_client_error(ex)

    ex = botocore.exceptions.ClientError({"Error": {"Code": "Not retryable"}}, "foo")  # pyright: ignore[reportAttributeAccessIssue]
    assert not _is_retriable_client_error(ex)

    ex = botocore.exceptions.ClientError({"Error": {"HTTPStatusCode": 505}}, "foo")  # pyright: ignore[reportAttributeAccessIssue]
    assert _is_retriable_client_error(ex)

    ex = botocore.exceptions.ClientError({"Error": {"HTTPStatusCode": 403}}, "foo")  # pyright: ignore[reportAttributeAccessIssue]
    assert not _is_retriable_client_error(ex)

    assert _is_retriable_client_error(ssl.SSLError("The read operation timed out"))
    assert not _is_retriable_client_error(ssl.SSLError("Unknown error"))

    assert _is_retriable_client_error(OSError(110, "Connection timed out"))
    assert not _is_retriable_client_error(OSError(12345, "Unknown error"))


def test_wrap_aws_client(mock_s3_resource):
    client = _wrap_aws_client(mock_s3_resource.meta.client, min_backoff=1000)
    res = client.list_buckets()
    assert res["ResponseMetadata"]["HTTPStatusCode"] == 200  # pyright: ignore[reportOptionalSubscript]
    assert res["Buckets"] == []  # pyright: ignore[reportOptionalSubscript]


def test_boto3_now():
    assert (
        time.mktime(_boto3_now().timetuple()) - time.mktime(datetime.now(tzutc()).timetuple()) < EPS
    )


def test_strip_microseconds():
    delta = timedelta(days=2, hours=1, minutes=3, seconds=20, milliseconds=123, microseconds=123)
    res = strip_microseconds(delta)
    assert res == timedelta(days=2, hours=1, minutes=3, seconds=20)
