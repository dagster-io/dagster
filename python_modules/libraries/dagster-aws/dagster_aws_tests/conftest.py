import boto3
import pytest
from moto import mock_rds, mock_rdsdata, mock_s3, mock_secretsmanager, mock_ssm


# Make sure unit tests never connect to real AWS
@pytest.fixture(autouse=True)
def fake_aws_credentials(monkeypatch):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "test")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "test")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")


@pytest.fixture
def mock_s3_resource():
    with mock_s3():
        yield boto3.resource("s3", region_name="us-east-1")


@pytest.fixture
def mock_s3_bucket(mock_s3_resource):
    yield mock_s3_resource.create_bucket(Bucket="test-bucket")


@pytest.fixture
def mock_secretsmanager_resource():
    with mock_secretsmanager():
        yield boto3.client("secretsmanager")


@pytest.fixture
def mock_ssm_client():
    with mock_ssm():
        yield boto3.client("ssm")


@pytest.fixture
def mock_rds_client():
    with mock_rds():
        yield boto3.client("rds")


@pytest.fixture
def mock_rds_data_client():
    with mock_rdsdata():
        yield boto3.client("rds-data")
