# pylint: disable=redefined-outer-name
import pytest

import boto3
from dagster_aws.athena.resources import FakeAthenaResource, AthenaError, AthenaTimeout
from moto import mock_athena


@pytest.fixture
def mock_athena_client(mock_s3_resource):  # pylint: disable=unused-argument
    with mock_athena():
        yield boto3.client("athena", region_name="us-east-1")


def test_execute_query(mock_athena_client):
    athena = FakeAthenaResource(client=mock_athena_client)
    assert athena.execute_query("SELECT 1", fetch_results=True) == [("1",)]
    assert athena.execute_query(
        "SELECT * FROM foo", fetch_results=True, expected_results=[(1, None), (2, 3)]
    ) == [("1",), ("2", "3")]


@pytest.mark.parametrize(
    "expected_states",
    [
        ["SUCCEEDED"],
        ["QUEUED", "SUCCEEDED"],
        ["QUEUED", "RUNNING", "SUCCEEDED"],
        ["QUEUED", "QUEUED", "SUCCEEDED"],
        ["QUEUED", "RUNNING", "RUNNING", "SUCCEEDED"],
    ],
)
def test_execute_query_state_transitions(mock_athena_client, expected_states):
    athena = FakeAthenaResource(client=mock_athena_client)
    athena.execute_query("SELECT 1", expected_states=expected_states)


@pytest.mark.parametrize(
    "expected_states",
    [
        ["FAILED"],
        ["CANCELLED"],
        ["QUEUED", "FAILED"],
        ["QUEUED", "RUNNING", "FAILED"],
        ["QUEUED", "CANCELLED"],
        ["QUEUED", "RUNNING", "CANCELLED"],
    ],
)
def test_execute_query_raises(mock_athena_client, expected_states):
    athena = FakeAthenaResource(client=mock_athena_client)
    with pytest.raises(AthenaError, match="state change reason"):
        athena.execute_query("SELECT 1", expected_states=expected_states)


def test_execute_query_timeout(mock_athena_client):
    athena = FakeAthenaResource(client=mock_athena_client, max_retries=1)
    with pytest.raises(AthenaTimeout):
        athena.execute_query("SELECT 1")
