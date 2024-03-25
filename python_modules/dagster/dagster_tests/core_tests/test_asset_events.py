from dagster import (
    AssetKey,
    AssetOut,
    DagsterEventType,
    EventRecordsFilter,
    Output,
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
        records = instance.get_event_records(
            EventRecordsFilter(
                DagsterEventType.ASSET_MATERIALIZATION_PLANNED,
                AssetKey("my_asset"),
            )
        )
        assert result.run_id == records[0].event_log_entry.run_id
        assert records[0].event_log_entry.dagster_event.step_key == "my_asset"


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
        records = instance.get_event_records(
            EventRecordsFilter(
                DagsterEventType.ASSET_MATERIALIZATION_PLANNED,
                AssetKey("my_asset_name"),
            )
        )
        assert result.run_id == records[0].event_log_entry.run_id
        assert all(
            record.event_log_entry.dagster_event.step_key == "my_asset" for record in records
        )


def _get_planned_run_ids(instance, asset_key):
    return [
        record.run_id
        for record in instance.get_event_records(
            EventRecordsFilter(
                event_type=DagsterEventType.ASSET_MATERIALIZATION_PLANNED,
                asset_key=asset_key,
            )
        )
    ]


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

        assert _get_planned_run_ids(instance, AssetKey("asset_one")) == [run_id]
        assert _get_planned_run_ids(instance, AssetKey("never_runs_asset")) == []

    with instance_for_test() as instance:  # fresh event log storage
        # test with both assets selected
        result = asset_job.execute_in_process(instance=instance, raise_on_error=False)
        run_id = result.run_id

        assert _get_planned_run_ids(instance, AssetKey("asset_one")) == [run_id]
        assert _get_planned_run_ids(instance, AssetKey("never_runs_asset")) == [run_id]


def test_non_assets_job_no_register_event():
    @op
    def my_op():
        pass

    @job
    def my_job():
        my_op()

    with instance_for_test() as instance:
        my_job.execute_in_process(instance=instance)
        intent_to_materialize_events = instance.get_event_records(
            EventRecordsFilter(DagsterEventType.ASSET_MATERIALIZATION_PLANNED)
        )

        assert intent_to_materialize_events == []


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
        materialize([my_asset], instance=instance)
        [run_id] = _get_planned_run_ids(instance, AssetKey("my_asset_name"))
        assert _get_planned_run_ids(instance, AssetKey("my_other_asset")) == [run_id]


def test_asset_partition_materialization_planned_events():
    @asset(partitions_def=StaticPartitionsDefinition(["a", "b"]))
    def my_asset():
        return 0

    @asset()
    def my_other_asset(my_asset):
        pass

    with instance_for_test() as instance:
        materialize_to_memory([my_asset, my_other_asset], instance=instance, partition_key="b")
        [record] = instance.get_event_records(
            EventRecordsFilter(
                DagsterEventType.ASSET_MATERIALIZATION_PLANNED,
                AssetKey("my_asset"),
            )
        )
        assert record.event_log_entry.dagster_event.event_specific_data.partition == "b"

        [record] = instance.get_event_records(
            EventRecordsFilter(
                DagsterEventType.ASSET_MATERIALIZATION_PLANNED,
                AssetKey("my_other_asset"),
            )
        )
        assert record.event_log_entry.dagster_event.event_specific_data.partition is None


def test_subset_on_asset_materialization_planned_event_for_single_run_backfill_allowed():
    partitions_def = StaticPartitionsDefinition(["a", "b", "c"])

    @asset(partitions_def=partitions_def)
    def my_asset():
        return 0

    with instance_for_test() as instance:
        materialize_to_memory(
            [my_asset],
            instance=instance,
            tags={ASSET_PARTITION_RANGE_START_TAG: "a", ASSET_PARTITION_RANGE_END_TAG: "b"},
        )

        [record] = instance.get_event_records(
            EventRecordsFilter(
                DagsterEventType.ASSET_MATERIALIZATION_PLANNED,
                AssetKey("my_asset"),
            )
        )
        assert (
            record.event_log_entry.dagster_event.event_specific_data.partitions_subset
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
        materialize_to_memory(
            [partitioned, unpartitioned],
            instance=instance,
            tags={ASSET_PARTITION_RANGE_START_TAG: "a", ASSET_PARTITION_RANGE_END_TAG: "b"},
        )

        [record] = instance.get_event_records(
            EventRecordsFilter(DagsterEventType.ASSET_MATERIALIZATION_PLANNED, partitioned.key)
        )
        assert (
            record.event_log_entry.dagster_event.event_specific_data.partitions_subset
            == partitions_def.subset_with_partition_keys(["a", "b"])
        )

        [record] = instance.get_event_records(
            EventRecordsFilter(DagsterEventType.ASSET_MATERIALIZATION_PLANNED, unpartitioned.key)
        )
        assert record.event_log_entry.dagster_event.event_specific_data.partitions_subset is None
