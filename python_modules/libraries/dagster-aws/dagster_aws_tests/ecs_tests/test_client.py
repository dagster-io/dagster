# pylint: disable=redefined-outer-name
import boto3
import pytest
from dagster_aws.ecs.client import ECSError, ECSTimeout, FakeECSClient
from moto import mock_ec2, mock_ecs


@pytest.fixture
def mock_ecs_client():
    with mock_ecs():
        yield boto3.client("ecs", region_name="us-east-2")


@pytest.fixture
def mock_ec2_resource():
    with mock_ec2():
        yield boto3.resource("ec2", region_name="us-east-2")


@pytest.fixture
def mock_subnets(mock_ec2_resource):
    vpc = mock_ec2_resource.create_vpc(CidrBlock="10.0.0.0/16")
    subnet = vpc.create_subnet(CidrBlock="10.0.0.0/24")
    return [subnet.id]


@pytest.fixture
def mock_ecs_cluster(mock_ecs_client):
    name = "test-cluster"
    mock_ecs_client.create_cluster(clusterName=name)
    return name


@pytest.fixture
def mock_ecs_task_definition(mock_ecs_client):
    task_definition = mock_ecs_client.register_task_definition(
        family="dagster",
        requiresCompatibilities=["FARGATE"],
        containerDefinitions=[{"name": "HelloWorld", "image": "hello-world:latest", "cpu": 256},],
        networkMode="awsvpc",
        cpu="256",
        memory="512",
    )
    return task_definition.get("taskDefinition").get("taskDefinitionArn")


@pytest.mark.parametrize(
    "expected_statuses",
    [
        ["STOPPED"],
        ["PROVISIONING", "STOPPED"],
        ["PENDING", "STOPPED"],
        ["ACTIVATING", "STOPPED"],
        ["RUNNING", "STOPPED"],
        ["DEACTIVATING", "STOPPED"],
        ["DEPROVISIONING", "STOPPED"],
    ],
)
def test_run_task(
    mock_ecs_client, mock_ecs_cluster, mock_ecs_task_definition, mock_subnets, expected_statuses
):
    client = FakeECSClient(cluster=mock_ecs_cluster, client=mock_ecs_client, subnets=mock_subnets)
    client.run_task(mock_ecs_task_definition, expected_statuses=expected_statuses)


def test_run_task_timeout(
    mock_ecs_client, mock_ecs_cluster, mock_ecs_task_definition, mock_subnets
):
    client = FakeECSClient(
        cluster=mock_ecs_cluster, client=mock_ecs_client, subnets=mock_subnets, max_polls=1
    )
    with pytest.raises(ECSTimeout):
        client.run_task(mock_ecs_task_definition)


def test_run_task_fails(mock_ecs_client, mock_ecs_cluster, mock_ecs_task_definition, mock_subnets):
    client = FakeECSClient(cluster=mock_ecs_cluster, subnets=mock_subnets, client=mock_ecs_client)
    with pytest.raises(ECSError, match="OutOfMemoryError"):
        client.run_task(mock_ecs_task_definition, expected_stop_code="OutOfMemoryError")
