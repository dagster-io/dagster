# pylint: disable=redefined-outer-name
import boto3
import moto
import pytest

from .stubbed_ecs import StubbedEcs


@pytest.fixture
def region():
    return "us-east-1"


@pytest.fixture
def ecs(region):
    return StubbedEcs(boto3.client("ecs", region_name=region))


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
def network_interface(subnet, security_group):
    return subnet.create_network_interface(Groups=[security_group.id])
