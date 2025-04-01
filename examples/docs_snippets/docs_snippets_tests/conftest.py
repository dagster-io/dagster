import boto3
import pytest
from moto import mock_s3

from dagster import file_relative_path


@pytest.fixture
def docs_snippets_folder():
    return file_relative_path(__file__, "../docs_snippets/")


@pytest.fixture
def mock_s3_resource():
    with mock_s3():
        yield boto3.resource("s3", region_name="us-east-1")


@pytest.fixture
def mock_s3_bucket(mock_s3_resource):
    yield mock_s3_resource.create_bucket(Bucket="test-bucket")
