import boto3
import moto
import pytest

from dagster_aws_tests.ecs_tests.stubbed_ecs import ThreadsafeStubbedEcs


@pytest.fixture
def region():
    return "us-east-1"


@pytest.fixture
def xregion():
    return "eu-central-1"


@pytest.fixture
def xregion_cluster_arn():
    return "xregion-cluster-arn"


@pytest.fixture
def ecs(region):
    return ThreadsafeStubbedEcs(region_name=region)


@pytest.fixture
def ecs_xregion(xregion):
    return ThreadsafeStubbedEcs(region_name=xregion)


@pytest.fixture
def ec2(region):
    with moto.mock_ec2():
        yield boto3.resource("ec2", region_name=region)


@pytest.fixture
def vpc(ec2):
    return ec2.create_vpc(CidrBlock="10.0.0.0/16")


@pytest.fixture
def subnet(vpc):
    return vpc.create_subnet(CidrBlock="10.0.0.0/24")


@pytest.fixture
def security_group(vpc):
    return vpc.create_security_group(Description="test", GroupName="test")


@pytest.fixture
def secrets_manager(region):
    with moto.mock_secretsmanager():
        yield boto3.client("secretsmanager", region_name=region)
