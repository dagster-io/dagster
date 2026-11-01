from unittest import mock
from uuid import uuid4

import pytest
from dagster import (
    AssetExecutionContext,
    DailyPartitionsDefinition,
    MultiPartitionsDefinition,
    StaticPartitionsDefinition,
    asset,
    materialize,
)
from dagster._core.errors import DagsterInvariantViolationError
from dagster_prefect.pipes_deployment import PipesPrefectDeploymentClient
from dagster_prefect.pipes_task import PIPES_PARAMS_TASK_ARGUMENT, PipesPrefectTaskClient
from dagster_prefect.resource import PrefectResource

from dagster_prefect_tests.conftest import DEPLOYMENT
from dagster_prefect_tests.test_pipes_deployment import RecordingDeploymentClient
from dagster_prefect_tests.test_pipes_task import RecordingTaskClient, summarize

DAILY = DailyPartitionsDefinition(start_date="2026-01-01")


def materialize_partition(client, partition_key: str | None = None, **run_kwargs):
    @asset(partitions_def=DAILY)
    def daily_report(context: AssetExecutionContext):
        return client.run(
            context=context, deployment=DEPLOYMENT, **run_kwargs
        ).get_materialize_result()

    return materialize([daily_report], partition_key=partition_key, raise_on_error=True)


def test_partition_key_is_passed_as_a_parameter(
    prefect_resource: PrefectResource, deployment: str
) -> None:
    client = RecordingDeploymentClient(prefect=prefect_resource, poll_interval_seconds=0)

    materialize_partition(client, "2026-03-04", partition_parameter="day")

    flow_run = prefect_resource.get_flow_run(client.launched[0].id)
    assert flow_run.parameters == {"day": "2026-03-04"}


def test_partition_time_window_is_passed_as_parameters(
    prefect_resource: PrefectResource, deployment: str
) -> None:
    client = RecordingDeploymentClient(prefect=prefect_resource, poll_interval_seconds=0)

    materialize_partition(
        client, "2026-03-04", partition_window_parameters=("window_start", "window_end")
    )

    flow_run = prefect_resource.get_flow_run(client.launched[0].id)
    # ISO strings, since Prefect parameters have to be JSON-serializable.
    assert flow_run.parameters["window_start"].startswith("2026-03-04T00:00:00")
    assert flow_run.parameters["window_end"].startswith("2026-03-05T00:00:00")


def test_caller_parameters_are_kept_alongside_the_partition(
    prefect_resource: PrefectResource, deployment: str
) -> None:
    client = RecordingDeploymentClient(prefect=prefect_resource, poll_interval_seconds=0)

    materialize_partition(
        client, "2026-03-04", parameters={"region": "eu"}, partition_parameter="day"
    )

    flow_run = prefect_resource.get_flow_run(client.launched[0].id)
    assert flow_run.parameters == {"region": "eu", "day": "2026-03-04"}


def test_nothing_is_added_when_not_asked_for(
    prefect_resource: PrefectResource, deployment: str
) -> None:
    """A flow that decides its own slice keeps working untouched."""
    client = RecordingDeploymentClient(prefect=prefect_resource, poll_interval_seconds=0)

    materialize_partition(client, "2026-03-04", parameters={"as_of": "latest"})

    flow_run = prefect_resource.get_flow_run(client.launched[0].id)
    assert flow_run.parameters == {"as_of": "latest"}


def test_backfill_launches_one_run_per_partition(
    prefect_resource: PrefectResource, deployment: str
) -> None:
    client = RecordingDeploymentClient(prefect=prefect_resource, poll_interval_seconds=0)
    days = ["2026-03-04", "2026-03-05", "2026-03-06"]

    for day in days:
        materialize_partition(client, day, partition_parameter="day")

    launched_days = [
        prefect_resource.get_flow_run(prefect_run.id).parameters["day"]
        for prefect_run in client.launched
    ]
    assert launched_days == days


def test_unpartitioned_asset_is_a_clear_error(
    prefect_resource: PrefectResource, deployment: str
) -> None:
    client = RecordingDeploymentClient(prefect=prefect_resource, poll_interval_seconds=0)

    @asset
    def not_partitioned(context: AssetExecutionContext):
        return client.run(
            context=context, deployment=DEPLOYMENT, partition_parameter="day"
        ).get_materialize_result()

    with pytest.raises(DagsterInvariantViolationError, match="does not target a partition"):
        materialize([not_partitioned], raise_on_error=True)


def test_multi_dimensional_partitions_are_a_clear_error(
    prefect_resource: PrefectResource, deployment: str
) -> None:
    client = RecordingDeploymentClient(prefect=prefect_resource, poll_interval_seconds=0)
    partitions_def = MultiPartitionsDefinition(
        {"day": DAILY, "region": StaticPartitionsDefinition(["eu", "us"])}
    )

    @asset(partitions_def=partitions_def)
    def by_day_and_region(context: AssetExecutionContext):
        return client.run(
            context=context, deployment=DEPLOYMENT, partition_parameter="day"
        ).get_materialize_result()

    with pytest.raises(
        DagsterInvariantViolationError, match="does not support multi-dimensional partitions"
    ):
        materialize([by_day_and_region], partition_key="2026-03-04|eu", raise_on_error=True)


def test_partition_key_is_passed_to_a_task(prefect_resource: PrefectResource) -> None:
    client = RecordingTaskClient(prefect=prefect_resource, poll_interval_seconds=0)

    @asset(partitions_def=DAILY)
    def daily_report(context: AssetExecutionContext):
        return client.run(
            context=context, task=summarize, partition_parameter="as_of"
        ).get_materialize_result()

    with mock.patch.object(summarize, "delay") as delay:
        delay.return_value = mock.Mock(task_run_id=uuid4())
        materialize([daily_report], partition_key="2026-03-04", raise_on_error=True)

    _, kwargs = delay.call_args
    assert kwargs["as_of"] == "2026-03-04"
    assert PIPES_PARAMS_TASK_ARGUMENT in kwargs


def test_clients_accept_the_same_partition_arguments() -> None:
    """Both launch paths take the same two arguments, so an asset can switch between them."""
    for client_type in (PipesPrefectDeploymentClient, PipesPrefectTaskClient):
        launch_parameters = client_type._launch.__annotations__  # noqa: SLF001
        assert "partition_parameter" in launch_parameters
        assert "partition_window_parameters" in launch_parameters
