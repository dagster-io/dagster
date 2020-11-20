import boto3
import pytest
from moto import mock_ecs


@pytest.fixture
def mock_ecs_client():
    with mock_ecs():
        yield boto3.client("ecs", region_name="us-east-2")


@pytest.fixture
def mock_ecs_cluster(mock_ecs_client):  # pylint: disable=redefined-outer-name
    name = "test-cluster"
    mock_ecs_client.create_cluster(clusterName="test-cluster")
    return name
