import os
import threading
from concurrent.futures import ThreadPoolExecutor
from unittest import mock

import dagster as dg
import pytest
from dagster import DagsterInstance, sensor
from dagster._core.definitions.assets.graph.asset_graph_subset import AssetGraphSubset
from dagster._core.definitions.events import AssetKeyPartitionKey
from dagster._core.definitions.run_request import InstigatorType, RunRequest
from dagster._core.execution.backfill import PartitionBackfill
from dagster._core.scheduler.instigation import InstigatorState, InstigatorStatus, TickStatus
from dagster._core.storage.tags import (
    ASSET_PARTITION_RANGE_END_TAG,
    ASSET_PARTITION_RANGE_START_TAG,
)
from dagster._core.test_utils import (
    create_test_daemon_workspace_context,
    freeze_time,
    load_remote_repo,
)
from dagster._core.workspace.load_target import ModuleTarget
from dagster._daemon import get_default_daemon_logger
from dagster._daemon.backfill import execute_backfill_iteration
from dagster._daemon.sensor import (
    BackfillSubmission,
    SkippedSensorBackfill,
    _submit_backfill_request,
)
from dagster._time import create_datetime
from dagster._vendored.dateutil.relativedelta import relativedelta

from dagster_tests.daemon_sensor_tests.test_sensor_run import evaluate_sensors, validate_tick

dynamic_partitions_def = dg.DynamicPartitionsDefinition(name="abc")


@dg.asset(partitions_def=dynamic_partitions_def)
def asset1() -> None: ...


@dg.asset(deps=[asset1])
def unpartitioned_child(): ...


def make_run_request_uses_backfill_daemon(context) -> dg.RunRequest:
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
    return dg.SensorResult(
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


@dg.asset(partitions_def=dg.StaticPartitionsDefinition(["a", "b", "c"]))
def static_partitioned_asset(): ...


@dg.asset(
    partitions_def=dg.StaticPartitionsDefinition(["a", "b", "c"]),
    config_schema={"value": str},
)
def public_partitioned_asset(): ...


@dg.asset(
    partitions_def=dg.StaticPartitionsDefinition(["a", "b", "c"]),
    backfill_policy=dg.BackfillPolicy.single_run(),
)
def single_run_partitioned_asset(): ...


public_dynamic_partitions_def = dg.DynamicPartitionsDefinition(name="public_dynamic_range")


@dg.asset(partitions_def=public_dynamic_partitions_def)
def public_dynamic_partitioned_asset(): ...


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

    yield dg.RunRequest(asset_selection=[static_partitioned_asset.key], partition_key="c")


@sensor(asset_selection=[public_partitioned_asset], minimum_interval_seconds=0)
def public_partition_range_backfill_request_sensor():
    return RunRequest.for_asset_partition_range(
        run_key="public-a-b",
        asset_selection=[public_partitioned_asset.key],
        partition_key_range=dg.PartitionKeyRange("a", "b"),
        run_config={"ops": {"public_partitioned_asset": {"config": {"value": "configured"}}}},
        tags={"tagkey": "tagvalue"},
    )


@sensor(asset_selection=[single_run_partitioned_asset])
def public_single_run_partition_range_backfill_request_sensor():
    return RunRequest.for_asset_partition_range(
        asset_selection=[single_run_partitioned_asset.key],
        partition_key_range=dg.PartitionKeyRange("a", "b"),
    )


@sensor(asset_selection=[public_dynamic_partitioned_asset])
def public_dynamic_partition_range_backfill_request_sensor():
    return dg.SensorResult(
        dynamic_partitions_requests=[public_dynamic_partitions_def.build_add_request(["a", "b"])],
        run_requests=[
            RunRequest.for_asset_partition_range(
                asset_selection=[public_dynamic_partitioned_asset.key],
                partition_key_range=dg.PartitionKeyRange("a", "b"),
            )
        ],
    )


defs = dg.Definitions(
    assets=dg.load_assets_from_current_module(),
    sensors=[
        sensor_result_backfill_request_sensor,
        return_backfill_request_sensor,
        yield_backfill_request_sensor,
        asset_outside_of_selection_backfill_request_sensor,
        invalid_partition_backfill_request_sensor,
        single_partition_run_request_sensor,
        backfill_and_run_request_sensor,
        public_partition_range_backfill_request_sensor,
        public_single_run_partition_range_backfill_request_sensor,
        public_dynamic_partition_range_backfill_request_sensor,
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
        repo = load_remote_repo(workspace_context, "__repository__")
        sensor = repo.get_sensor(sensor_name)

        instance.add_instigator_state(
            InstigatorState(
                sensor.get_remote_origin(),
                InstigatorType.SENSOR,
                InstigatorStatus.RUNNING,
            )
        )
        evaluate_sensors(workspace_context, executor)

        assert instance.get_runs_count() == 0
        ticks = instance.get_ticks(sensor.get_remote_origin_id(), sensor.selector_id)
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
            sensor,
            None,
            TickStatus.SUCCESS,
            expected_run_ids=[backfill.backfill_id],
        )


def test_asset_selection_outside_of_range(instance, executor):
    with create_test_daemon_workspace_context(
        workspace_load_target=module_target, instance=instance
    ) as workspace_context:
        repo = load_remote_repo(workspace_context, "__repository__")
        sensor = repo.get_sensor(asset_outside_of_selection_backfill_request_sensor.name)

        instance.add_instigator_state(
            InstigatorState(
                sensor.get_remote_origin(),
                InstigatorType.SENSOR,
                InstigatorStatus.RUNNING,
            )
        )
        evaluate_sensors(workspace_context, executor)
        ticks = instance.get_ticks(sensor.get_remote_origin_id(), sensor.selector_id)

        validate_tick(
            ticks[0],
            remote_sensor=sensor,
            expected_status=TickStatus.FAILURE,
            expected_datetime=None,
            expected_error="RunRequest includes asset keys that are not part of sensor's "
            "asset_selection: {AssetKey(['static_partitioned_asset'])}",
        )


def test_invalid_partition(instance, executor):
    with create_test_daemon_workspace_context(
        workspace_load_target=module_target, instance=instance
    ) as workspace_context:
        repo = load_remote_repo(workspace_context, "__repository__")
        sensor = repo.get_sensor(invalid_partition_backfill_request_sensor.name)

        instance.add_instigator_state(
            InstigatorState(
                sensor.get_remote_origin(),
                InstigatorType.SENSOR,
                InstigatorStatus.RUNNING,
            )
        )
        evaluate_sensors(workspace_context, executor)
        ticks = instance.get_ticks(sensor.get_remote_origin_id(), sensor.selector_id)

        # allow creating a backfill with an invalid partition. it will get caught in the daemon
        # and show up as an error there.
        validate_tick(ticks[0], sensor, None, TickStatus.SUCCESS)


def test_single_partition(instance, executor):
    """Tests requesting a single partition using asset_graph_subset, which will be executed as a backfill.
    However, when we add additional introspection on the asset_graph_subset to determine how each request
    should be executed, this test should launch a single run instead.
    """
    with create_test_daemon_workspace_context(
        workspace_load_target=module_target, instance=instance
    ) as workspace_context:
        repo = load_remote_repo(workspace_context, "__repository__")
        sensor = repo.get_sensor(single_partition_run_request_sensor.name)

        instance.add_instigator_state(
            InstigatorState(
                sensor.get_remote_origin(),
                InstigatorType.SENSOR,
                InstigatorStatus.RUNNING,
            )
        )
        evaluate_sensors(workspace_context, executor)
        ticks = instance.get_ticks(sensor.get_remote_origin_id(), sensor.selector_id)

        backfills = instance.get_backfills()
        assert len(backfills) == 1
        backfill = backfills[0]

        validate_tick(
            ticks[0],
            sensor,
            None,
            TickStatus.SUCCESS,
            expected_run_ids=[backfill.backfill_id],
        )


def test_backfill_and_run_request(instance, executor):
    with create_test_daemon_workspace_context(
        workspace_load_target=module_target, instance=instance
    ) as workspace_context:
        repo = load_remote_repo(workspace_context, "__repository__")
        sensor = repo.get_sensor(backfill_and_run_request_sensor.name)

        instance.add_instigator_state(
            InstigatorState(
                sensor.get_remote_origin(),
                InstigatorType.SENSOR,
                InstigatorStatus.RUNNING,
            )
        )
        evaluate_sensors(workspace_context, executor)
        ticks = instance.get_ticks(sensor.get_remote_origin_id(), sensor.selector_id)

        backfills = instance.get_backfills()
        assert len(backfills) == 1
        backfill = backfills[0]

        runs = instance.get_runs()
        assert len(runs) == 1
        run = runs[0]

        validate_tick(
            ticks[0],
            sensor,
            None,
            TickStatus.SUCCESS,
            expected_run_ids=[backfill.backfill_id, run.run_id],
        )


def test_public_partition_range_backfill_request(instance, executor):
    freeze_datetime = create_datetime(year=2019, month=2, day=27, hour=23, minute=59, second=59)
    with create_test_daemon_workspace_context(
        workspace_load_target=module_target, instance=instance
    ) as workspace_context:
        repo = load_remote_repo(workspace_context, "__repository__")
        sensor = repo.get_sensor(public_partition_range_backfill_request_sensor.name)

        instance.add_instigator_state(
            InstigatorState(
                sensor.get_remote_origin(),
                InstigatorType.SENSOR,
                InstigatorStatus.RUNNING,
            )
        )
        with freeze_time(freeze_datetime):
            evaluate_sensors(workspace_context, executor)

        backfills = instance.get_backfills()
        assert len(backfills) == 1
        backfill = backfills[0]
        assert backfill.tags.get("tagkey") == "tagvalue"
        assert backfill.run_config == {
            "ops": {"public_partitioned_asset": {"config": {"value": "configured"}}}
        }
        assert backfill.asset_backfill_data
        assert set(backfill.asset_backfill_data.target_subset.iterate_asset_partitions()) == {
            AssetKeyPartitionKey(public_partitioned_asset.key, "a"),
            AssetKeyPartitionKey(public_partitioned_asset.key, "b"),
        }

        assert all(
            not error
            for error in execute_backfill_iteration(
                workspace_context, get_default_daemon_logger("BackfillDaemon")
            )
        )
        runs = instance.get_runs()
        assert len(runs) == 2
        for run in runs:
            assert run.tags.get("tagkey") == "tagvalue"
            assert run.run_config == {
                "ops": {"public_partitioned_asset": {"config": {"value": "configured"}}}
            }

        with freeze_time(freeze_datetime + relativedelta(seconds=60)):
            evaluate_sensors(workspace_context, executor)
        assert len(instance.get_backfills()) == 1
        ticks = instance.get_ticks(sensor.get_remote_origin_id(), sensor.selector_id)
        assert len(ticks) == 2
        validate_tick(ticks[0], sensor, None, TickStatus.SKIPPED)
        assert ticks[0].run_keys == ["public-a-b"]
        assert not ticks[0].run_ids


def test_duplicate_partition_range_run_key_with_concurrent_submission(instance):
    with create_test_daemon_workspace_context(
        workspace_load_target=module_target, instance=instance
    ) as workspace_context:
        repo = load_remote_repo(workspace_context, "__repository__")
        sensor = repo.get_sensor(public_partition_range_backfill_request_sensor.name)
        run_request = RunRequest(
            run_key="duplicate-public-a-b",
            asset_graph_subset=AssetGraphSubset.from_asset_partition_set(
                asset_partitions_set={
                    AssetKeyPartitionKey(public_partitioned_asset.key, "a"),
                    AssetKeyPartitionKey(public_partitioned_asset.key, "b"),
                },
                asset_graph=defs.get_repository_def().asset_graph,
            ),
        )

        construction_barrier = threading.Barrier(2)
        original_from_asset_graph_subset = PartitionBackfill.from_asset_graph_subset
        existing_backfills_by_key: dict[str, PartitionBackfill] = {}
        backfill_submission_lock = threading.Lock()

        def synchronized_from_asset_graph_subset(*args, **kwargs):
            construction_barrier.wait(timeout=5)
            return original_from_asset_graph_subset(*args, **kwargs)

        with (
            mock.patch.object(
                PartitionBackfill,
                "from_asset_graph_subset",
                side_effect=synchronized_from_asset_graph_subset,
            ),
            ThreadPoolExecutor(max_workers=2) as submit_executor,
        ):
            results = [
                future.result()
                for future in [
                    submit_executor.submit(
                        _submit_backfill_request,
                        backfill_id=f"backfill-{index}",
                        run_request=run_request,
                        instance=instance,
                        remote_sensor=sensor,
                        existing_backfills_by_key=existing_backfills_by_key,
                        backfill_submission_lock=backfill_submission_lock,
                    )
                    for index in range(2)
                ]
            ]

        backfills = instance.get_backfills()
        assert len(backfills) == 1
        assert sum(isinstance(result.run, BackfillSubmission) for result in results) == 1
        assert sum(isinstance(result.run, SkippedSensorBackfill) for result in results) == 1


def test_public_partition_range_backfill_uses_single_run_policy(instance, executor):
    with create_test_daemon_workspace_context(
        workspace_load_target=module_target, instance=instance
    ) as workspace_context:
        repo = load_remote_repo(workspace_context, "__repository__")
        sensor = repo.get_sensor(public_single_run_partition_range_backfill_request_sensor.name)
        instance.add_instigator_state(
            InstigatorState(
                sensor.get_remote_origin(),
                InstigatorType.SENSOR,
                InstigatorStatus.RUNNING,
            )
        )

        evaluate_sensors(workspace_context, executor)
        assert all(
            not error
            for error in execute_backfill_iteration(
                workspace_context, get_default_daemon_logger("BackfillDaemon")
            )
        )

        runs = instance.get_runs()
        assert len(runs) == 1
        assert runs[0].tags[ASSET_PARTITION_RANGE_START_TAG] == "a"
        assert runs[0].tags[ASSET_PARTITION_RANGE_END_TAG] == "b"


def test_public_partition_range_backfill_with_pending_dynamic_partitions(instance, executor):
    with create_test_daemon_workspace_context(
        workspace_load_target=module_target, instance=instance
    ) as workspace_context:
        repo = load_remote_repo(workspace_context, "__repository__")
        sensor = repo.get_sensor(public_dynamic_partition_range_backfill_request_sensor.name)
        instance.add_instigator_state(
            InstigatorState(
                sensor.get_remote_origin(),
                InstigatorType.SENSOR,
                InstigatorStatus.RUNNING,
            )
        )

        evaluate_sensors(workspace_context, executor)

        assert instance.get_dynamic_partitions(public_dynamic_partitions_def.name) == ["a", "b"]
        backfills = instance.get_backfills()
        assert len(backfills) == 1
        assert backfills[0].asset_backfill_data
        assert set(backfills[0].asset_backfill_data.target_subset.iterate_asset_partitions()) == {
            AssetKeyPartitionKey(public_dynamic_partitioned_asset.key, "a"),
            AssetKeyPartitionKey(public_dynamic_partitioned_asset.key, "b"),
        }
