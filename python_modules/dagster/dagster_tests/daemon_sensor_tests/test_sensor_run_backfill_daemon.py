import os

import pytest
from dagster import (
    DagsterInstance,
    Definitions,
    DynamicPartitionsDefinition,
    SensorResult,
    StaticPartitionsDefinition,
    asset,
    load_assets_from_current_module,
    sensor,
)
from dagster._core.definitions.asset_graph_subset import AssetGraphSubset
from dagster._core.definitions.events import AssetKeyPartitionKey
from dagster._core.definitions.run_request import InstigatorType, RunRequest
from dagster._core.scheduler.instigation import InstigatorState, InstigatorStatus, TickStatus
from dagster._core.test_utils import create_test_daemon_workspace_context, load_external_repo
from dagster._core.workspace.load_target import ModuleTarget

from dagster_tests.daemon_sensor_tests.test_sensor_run import evaluate_sensors, validate_tick

dynamic_partitions_def = DynamicPartitionsDefinition(name="abc")


@asset(partitions_def=dynamic_partitions_def)
def asset1() -> None: ...


@asset(deps=[asset1])
def unpartitioned_child(): ...


def make_run_request_uses_backfill_daemon(context) -> RunRequest:
    ags = AssetGraphSubset.from_asset_partition_set(
        asset_partitions_set={
            AssetKeyPartitionKey(asset1.key, "foo"),
            AssetKeyPartitionKey(asset1.key, "bar"),
            AssetKeyPartitionKey(unpartitioned_child.key, None),
        },
        asset_graph=context.repository_def.asset_graph,
    )
    return RunRequest.for_asset_graph_subset(
        asset_graph_subset=ags,
        tags={"tagkey": "tagvalue"},
    )


@sensor(asset_selection=[asset1, unpartitioned_child])
def sensor_result_backfill_request_sensor(context):
    return SensorResult(
        dynamic_partitions_requests=[dynamic_partitions_def.build_add_request(["foo", "bar"])],
        run_requests=[make_run_request_uses_backfill_daemon(context)],
    )


@sensor(asset_selection=[asset1, unpartitioned_child])
def return_backfill_request_sensor(context):
    context.instance.add_dynamic_partitions(dynamic_partitions_def.name, ["foo", "bar"])
    return make_run_request_uses_backfill_daemon(context)


@sensor(asset_selection=[asset1, unpartitioned_child])
def yield_backfill_request_sensor(context):
    context.instance.add_dynamic_partitions(dynamic_partitions_def.name, ["foo", "bar"])
    yield make_run_request_uses_backfill_daemon(context)


@asset(partitions_def=StaticPartitionsDefinition(["a", "b", "c"]))
def static_partitioned_asset(): ...


@sensor(asset_selection=[asset1, unpartitioned_child])
def asset_outside_of_selection_backfill_request_sensor(context):
    ags = AssetGraphSubset.from_asset_partition_set(
        asset_partitions_set={
            AssetKeyPartitionKey(static_partitioned_asset.key, "a"),
            AssetKeyPartitionKey(static_partitioned_asset.key, "b"),
        },
        asset_graph=context.repository_def.asset_graph,
    )
    return RunRequest.for_asset_graph_subset(
        asset_graph_subset=ags,
        tags={"tagkey": "tagvalue"},
    )


@sensor(asset_selection=[static_partitioned_asset])
def invalid_partition_backfill_request_sensor(context):
    ags = AssetGraphSubset.from_asset_partition_set(
        asset_partitions_set={
            AssetKeyPartitionKey(static_partitioned_asset.key, "b"),
            AssetKeyPartitionKey(static_partitioned_asset.key, "z"),
        },
        asset_graph=context.repository_def.asset_graph,
    )
    return RunRequest.for_asset_graph_subset(
        asset_graph_subset=ags,
        tags={"tagkey": "tagvalue"},
    )


@sensor(asset_selection=[static_partitioned_asset])
def single_partition_run_request_sensor(context):
    ags = AssetGraphSubset.from_asset_partition_set(
        asset_partitions_set={AssetKeyPartitionKey(static_partitioned_asset.key, "b")},
        asset_graph=context.repository_def.asset_graph,
    )
    return RunRequest.for_asset_graph_subset(
        asset_graph_subset=ags,
        tags={"tagkey": "tagvalue"},
    )


@sensor(asset_selection=[static_partitioned_asset])
def backfill_and_run_request_sensor(context):
    ags = AssetGraphSubset.from_asset_partition_set(
        asset_partitions_set={
            AssetKeyPartitionKey(static_partitioned_asset.key, "a"),
            AssetKeyPartitionKey(static_partitioned_asset.key, "b"),
        },
        asset_graph=context.repository_def.asset_graph,
    )
    yield RunRequest.for_asset_graph_subset(asset_graph_subset=ags, tags={"tagkey": "tagvalue"})

    yield RunRequest(asset_selection=[static_partitioned_asset.key], partition_key="c")


defs = Definitions(
    assets=load_assets_from_current_module(),
    sensors=[
        sensor_result_backfill_request_sensor,
        return_backfill_request_sensor,
        yield_backfill_request_sensor,
        asset_outside_of_selection_backfill_request_sensor,
        invalid_partition_backfill_request_sensor,
        single_partition_run_request_sensor,
        backfill_and_run_request_sensor,
    ],
)

module_target = ModuleTarget(
    module_name="dagster_tests.daemon_sensor_tests.test_sensor_run_backfill_daemon",
    attribute=None,
    working_directory=os.path.join(os.path.dirname(__file__), "..", ".."),
    location_name="test_location",
)


@pytest.mark.parametrize(
    "sensor_name",
    [
        "sensor_result_backfill_request_sensor",
        "return_backfill_request_sensor",
        "yield_backfill_request_sensor",
    ],
)
def test_backfill_request_sensor(instance: DagsterInstance, executor, sensor_name: str):
    with create_test_daemon_workspace_context(
        workspace_load_target=module_target, instance=instance
    ) as workspace_context:
        external_repo = load_external_repo(workspace_context, "__repository__")
        external_sensor = external_repo.get_external_sensor(sensor_name)

        instance.add_instigator_state(
            InstigatorState(
                external_sensor.get_external_origin(),
                InstigatorType.SENSOR,
                InstigatorStatus.RUNNING,
            )
        )
        evaluate_sensors(workspace_context, executor)

        assert instance.get_runs_count() == 0
        ticks = instance.get_ticks(
            external_sensor.get_external_origin_id(), external_sensor.selector_id
        )
        assert len(ticks) == 1

        backfills = instance.get_backfills()
        assert len(backfills) == 1
        backfill = backfills[0]
        assert backfill.tags.get("tagkey") == "tagvalue"
        assert backfill.is_asset_backfill
        asset_backfill_data = backfill.asset_backfill_data
        assert asset_backfill_data
        assert set(asset_backfill_data.target_subset.iterate_asset_partitions()) == {
            AssetKeyPartitionKey(asset1.key, "foo"),
            AssetKeyPartitionKey(asset1.key, "bar"),
            AssetKeyPartitionKey(unpartitioned_child.key, None),
        }

        validate_tick(
            ticks[0],
            external_sensor,
            None,
            TickStatus.SUCCESS,
            expected_run_ids=[backfill.backfill_id],
        )


def test_asset_selection_outside_of_range(instance, executor):
    with create_test_daemon_workspace_context(
        workspace_load_target=module_target, instance=instance
    ) as workspace_context:
        external_repo = load_external_repo(workspace_context, "__repository__")
        external_sensor = external_repo.get_external_sensor(
            asset_outside_of_selection_backfill_request_sensor.name
        )

        instance.add_instigator_state(
            InstigatorState(
                external_sensor.get_external_origin(),
                InstigatorType.SENSOR,
                InstigatorStatus.RUNNING,
            )
        )
        evaluate_sensors(workspace_context, executor)
        ticks = instance.get_ticks(
            external_sensor.get_external_origin_id(), external_sensor.selector_id
        )

        validate_tick(
            ticks[0],
            external_sensor=external_sensor,
            expected_status=TickStatus.FAILURE,
            expected_datetime=None,
            expected_error="RunRequest includes asset keys that are not part of sensor's "
            "asset_selection: {AssetKey(['static_partitioned_asset'])}",
        )


def test_invalid_partition(instance, executor):
    with create_test_daemon_workspace_context(
        workspace_load_target=module_target, instance=instance
    ) as workspace_context:
        external_repo = load_external_repo(workspace_context, "__repository__")
        external_sensor = external_repo.get_external_sensor(
            invalid_partition_backfill_request_sensor.name
        )

        instance.add_instigator_state(
            InstigatorState(
                external_sensor.get_external_origin(),
                InstigatorType.SENSOR,
                InstigatorStatus.RUNNING,
            )
        )
        evaluate_sensors(workspace_context, executor)
        ticks = instance.get_ticks(
            external_sensor.get_external_origin_id(), external_sensor.selector_id
        )

        # allow creating a backfill with an invalid partition. it will get caught in the daemon
        # and show up as an error there.
        validate_tick(ticks[0], external_sensor, None, TickStatus.SUCCESS)


def test_single_partition(instance, executor):
    """Tests requesting a single partition using asset_graph_subset, which will be executed as a backfill.
    However, when we add additional introspection on the asset_graph_subset to determine how each request
    should be executed, this test should launch a single run instead.
    """
    with create_test_daemon_workspace_context(
        workspace_load_target=module_target, instance=instance
    ) as workspace_context:
        external_repo = load_external_repo(workspace_context, "__repository__")
        external_sensor = external_repo.get_external_sensor(
            single_partition_run_request_sensor.name
        )

        instance.add_instigator_state(
            InstigatorState(
                external_sensor.get_external_origin(),
                InstigatorType.SENSOR,
                InstigatorStatus.RUNNING,
            )
        )
        evaluate_sensors(workspace_context, executor)
        ticks = instance.get_ticks(
            external_sensor.get_external_origin_id(), external_sensor.selector_id
        )

        backfills = instance.get_backfills()
        assert len(backfills) == 1
        backfill = backfills[0]

        validate_tick(
            ticks[0],
            external_sensor,
            None,
            TickStatus.SUCCESS,
            expected_run_ids=[backfill.backfill_id],
        )


def test_backfill_and_run_request(instance, executor):
    with create_test_daemon_workspace_context(
        workspace_load_target=module_target, instance=instance
    ) as workspace_context:
        external_repo = load_external_repo(workspace_context, "__repository__")
        external_sensor = external_repo.get_external_sensor(backfill_and_run_request_sensor.name)

        instance.add_instigator_state(
            InstigatorState(
                external_sensor.get_external_origin(),
                InstigatorType.SENSOR,
                InstigatorStatus.RUNNING,
            )
        )
        evaluate_sensors(workspace_context, executor)
        ticks = instance.get_ticks(
            external_sensor.get_external_origin_id(), external_sensor.selector_id
        )

        backfills = instance.get_backfills()
        assert len(backfills) == 1
        backfill = backfills[0]

        runs = instance.get_runs()
        assert len(runs) == 1
        run = runs[0]

        validate_tick(
            ticks[0],
            external_sensor,
            None,
            TickStatus.SUCCESS,
            expected_run_ids=[backfill.backfill_id, run.run_id],
        )
