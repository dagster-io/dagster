import boto3
import pytest

from .stubbed_ecs import StubbedEcs


@pytest.fixture
def ecs():
    return StubbedEcs(boto3.client("ecs", region_name="us-east-1"))
