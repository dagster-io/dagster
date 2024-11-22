from typing import Set

from dagster import (
    AssetKey,
    AssetOut,
    DagsterEventType,
    Output,
    _check as check,
    asset,
    job,
    materialize_to_memory,
    multi_asset,
    op,
)
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.materialize import materialize
from dagster._core.definitions.partition import StaticPartitionsDefinition
from dagster._core.storage.tags import (
    ASSET_PARTITION_RANGE_END_TAG,
    ASSET_PARTITION_RANGE_START_TAG,
)
from dagster._core.test_utils import instance_for_test


def test_asset_mat_planned_event_step_key():
    @asset
    def my_asset():
        return 0

    with instance_for_test() as instance:
        result = materialize([my_asset], instance=instance)
        planned_events = _get_planned_events(instance, result.run_id)
        assert len(planned_events) == 1
        planned_event = planned_events[0]
        assert planned_event.event_specific_data.asset_key == AssetKey("my_asset")
        assert planned_event.step_key == "my_asset"


def test_multi_asset_mat_planned_event_step_key():
    @multi_asset(
        outs={
            "my_out_name": AssetOut(key=AssetKey("my_asset_name")),
            "my_other_out_name": AssetOut(key=AssetKey("my_other_asset")),
        }
    )
    def my_asset():
        yield Output(1, "my_out_name")
        yield Output(2, "my_other_out_name")

    with instance_for_test() as instance:
        result = materialize([my_asset], instance=instance)
        planned_events = _get_planned_events(instance, result.run_id)
        assert len(planned_events) == 2
        assert all(event.is_asset_materialization_planned for event in planned_events)
        assert all(event.step_key == "my_asset" for event in planned_events)
        assert set(event.asset_key for event in planned_events) == {
            AssetKey("my_asset_name"),
            AssetKey("my_other_asset"),
        }


def _get_planned_events(instance, run_id):
    records = instance.get_records_for_run(
        run_id, of_type=DagsterEventType.ASSET_MATERIALIZATION_PLANNED
    ).records
    planned_events = [record.event_log_entry.dagster_event for record in records]
    assert all(event.is_asset_materialization_planned for event in planned_events)
    return planned_events


def _get_planned_asset_keys_from_event_log(instance, run_id):
    return set(event.asset_key for event in _get_planned_events(instance, run_id))


def _get_planned_asset_keys_from_execution_plan_snapshot(instance, run_id) -> set[AssetKey]:
    run = check.not_none(instance.get_run_by_id(run_id))

    execution_plan_snapshot = instance.get_execution_plan_snapshot(run.execution_plan_snapshot_id)

    return execution_plan_snapshot.asset_selection


def test_asset_materialization_planned_event_yielded():
    @asset
    def asset_one():
        raise Exception("foo")

    @asset
    def never_runs_asset(asset_one):
        return asset_one

    asset_job = Definitions(
        assets=[asset_one, never_runs_asset],
    ).get_implicit_global_asset_job_def()

    with instance_for_test() as instance:
        # test with only one asset selected
        result = asset_job.execute_in_process(
            instance=instance, raise_on_error=False, op_selection=["asset_one"]
        )
        run_id = result.run_id

        assert _get_planned_asset_keys_from_event_log(instance, run_id) == {AssetKey("asset_one")}
        assert _get_planned_asset_keys_from_execution_plan_snapshot(instance, run_id) == {
            AssetKey("asset_one")
        }

    with instance_for_test() as instance:  # fresh event log storage
        # test with both assets selected
        result = asset_job.execute_in_process(instance=instance, raise_on_error=False)
        run_id = result.run_id

        assert _get_planned_asset_keys_from_event_log(instance, run_id) == {
            AssetKey("asset_one"),
            AssetKey("never_runs_asset"),
        }
        assert _get_planned_asset_keys_from_execution_plan_snapshot(instance, run_id) == {
            AssetKey("asset_one"),
            AssetKey("never_runs_asset"),
        }


def test_non_assets_job_no_register_event():
    @op
    def my_op():
        pass

    @job
    def my_job():
        my_op()

    with instance_for_test() as instance:
        result = my_job.execute_in_process(instance=instance)
        assert _get_planned_events(instance, result.run_id) == []


def test_multi_asset_asset_materialization_planned_events():
    @multi_asset(
        outs={
            "my_out_name": AssetOut(key=AssetKey("my_asset_name")),
            "my_other_out_name": AssetOut(key=AssetKey("my_other_asset")),
        }
    )
    def my_asset():
        yield Output(1, "my_out_name")
        yield Output(2, "my_other_out_name")

    with instance_for_test() as instance:
        result = materialize([my_asset], instance=instance)
        assert _get_planned_asset_keys_from_event_log(instance, result.run_id) == {
            AssetKey("my_asset_name"),
            AssetKey("my_other_asset"),
        }
        assert _get_planned_asset_keys_from_execution_plan_snapshot(instance, result.run_id) == {
            AssetKey("my_asset_name"),
            AssetKey("my_other_asset"),
        }


def test_asset_partition_materialization_planned_events():
    @asset(partitions_def=StaticPartitionsDefinition(["a", "b"]))
    def my_asset():
        return 0

    @asset()
    def my_other_asset(my_asset):
        pass

    with instance_for_test() as instance:
        result = materialize_to_memory(
            [my_asset, my_other_asset], instance=instance, partition_key="b"
        )
        planned_events = _get_planned_events(instance, result.run_id)
        assert len(planned_events) == 2
        [my_asset_event] = [
            event for event in planned_events if event.asset_key == AssetKey("my_asset")
        ]
        [my_other_asset_event] = [
            event for event in planned_events if event.asset_key == AssetKey("my_other_asset")
        ]
        assert my_asset_event.event_specific_data.partition == "b"
        assert my_other_asset_event.event_specific_data.partition is None


def test_subset_on_asset_materialization_planned_event_for_single_run_backfill_allowed():
    partitions_def = StaticPartitionsDefinition(["a", "b", "c"])

    @asset(partitions_def=partitions_def)
    def my_asset():
        return 0

    with instance_for_test() as instance:
        result = materialize_to_memory(
            [my_asset],
            instance=instance,
            tags={ASSET_PARTITION_RANGE_START_TAG: "a", ASSET_PARTITION_RANGE_END_TAG: "b"},
        )

        planned_events = _get_planned_events(instance, result.run_id)
        assert len(planned_events) == 1
        planned_event = planned_events[0]
        assert planned_event.asset_key == AssetKey("my_asset")
        assert (
            planned_event.event_specific_data.partitions_subset
            == partitions_def.subset_with_partition_keys(["a", "b"])
        )


def test_single_run_backfill_with_unpartitioned_and_partitioned_mix():
    partitions_def = StaticPartitionsDefinition(["a", "b", "c"])

    @asset(partitions_def=partitions_def)
    def partitioned():
        return 0

    @asset
    def unpartitioned():
        return 0

    with instance_for_test() as instance:
        result = materialize_to_memory(
            [partitioned, unpartitioned],
            instance=instance,
            tags={ASSET_PARTITION_RANGE_START_TAG: "a", ASSET_PARTITION_RANGE_END_TAG: "b"},
        )

        planned_events = _get_planned_events(instance, result.run_id)
        assert len(planned_events) == 2
        [partitioned_event] = [
            event for event in planned_events if event.asset_key == partitioned.key
        ]
        [unpartitioned_event] = [
            event for event in planned_events if event.asset_key == unpartitioned.key
        ]
        assert (
            partitioned_event.event_specific_data.partitions_subset
            == partitions_def.subset_with_partition_keys(["a", "b"])
        )
        assert unpartitioned_event.event_specific_data.partitions_subset is None
