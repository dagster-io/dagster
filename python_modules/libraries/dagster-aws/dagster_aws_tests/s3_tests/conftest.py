import boto3
import pytest
from moto import mock_s3


@pytest.fixture
def s3():
    with mock_s3():
        yield boto3.resource("s3")


@pytest.fixture
def bucket(s3):  # pylint: disable=redefined-outer-name
    yield s3.create_bucket(Bucket="test-bucket")
