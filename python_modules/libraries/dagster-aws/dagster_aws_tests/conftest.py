import boto3
import pytest
from moto import mock_s3


@pytest.fixture
def mock_s3_resource():
    with mock_s3():
        yield boto3.resource("s3", region_name="us-east-1")


@pytest.fixture
def mock_s3_bucket(mock_s3_resource):  # pylint: disable=redefined-outer-name
    yield mock_s3_resource.create_bucket(Bucket="test-bucket")
