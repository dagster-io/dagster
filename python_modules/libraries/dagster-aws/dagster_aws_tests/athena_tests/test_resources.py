import boto3
import pytest
from moto import mock_athena

from dagster_aws.athena.resources import (
    AthenaError,
    AthenaTimeout,
    FakeAthenaClient,
    ResourceWithAthenaConfig,
    fake_athena_resource,
)


class TestAthenaClientResource(ResourceWithAthenaConfig):
    def get_client(self) -> FakeAthenaClient:
        return FakeAthenaClient(
            client=boto3.client("athena", region_name="us-east-1"),
            workgroup=self.workgroup,
            polling_interval=self.polling_interval,
            max_polls=self.max_polls,
        )


@pytest.fixture
def mock_athena_client(mock_s3_resource):
    with mock_athena():
        yield boto3.client("athena", region_name="us-east-1")


def test_execute_query(mock_athena_client):
    athena = FakeAthenaClient(client=mock_athena_client)
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
    athena = FakeAthenaClient(client=mock_athena_client)
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
    athena = FakeAthenaClient(client=mock_athena_client)
    with pytest.raises(AthenaError, match="state change reason"):
        athena.execute_query("SELECT 1", expected_states=expected_states)


def test_execute_query_timeout(mock_athena_client):
    athena = FakeAthenaClient(client=mock_athena_client, max_polls=1)
    with pytest.raises(AthenaTimeout):
        athena.execute_query("SELECT 1")


def test_execute_query_succeeds_on_last_poll(mock_athena_client):
    athena = FakeAthenaClient(client=mock_athena_client, max_polls=1)
    athena.execute_query("SELECT 1", expected_states=["SUCCEEDED"])


def test_op(mock_athena_client) -> None:
    from dagster import build_op_context, op

    @op(required_resource_keys={"athena"})
    def example_athena_op(context):
        return context.resources.athena.execute_query("SELECT 1", fetch_results=True)

    context = build_op_context(resources={"athena": fake_athena_resource})
    assert example_athena_op(context) == [("1",)]


def test_op_pythonic_resource(mock_athena_client) -> None:
    from dagster import op

    @op
    def example_athena_op(athena: TestAthenaClientResource):
        return athena.get_client().execute_query("SELECT 1", fetch_results=True)

    assert example_athena_op(athena=TestAthenaClientResource.configure_at_launch()) == [("1",)]
