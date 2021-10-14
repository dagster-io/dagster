import os

import boto3
import pytest
from botocore.exceptions import ClientError
from dagster_aws.version import __version__


def test_version():
    assert __version__


# Make sure unit tests never connect to real AWS
def test_fake_aws_credentials():
    assert os.environ["AWS_ACCESS_KEY_ID"] == "test"
    assert os.environ["AWS_SECRET_ACCESS_KEY"] == "test"

    with pytest.raises(ClientError):
        boto3.client("s3").list_buckets()
