from dagster import (
    In,
    AssetKey,
    DagsterEventType,
    EventRecordsFilter,
    Out,
    Output,
    asset,
    job,
    multi_asset,
    op,
)
from dagster._core.test_utils import instance_for_test
from dagster._legacy import build_assets_job


def test_asset_materialization_planned_event_yielded():
    @asset
    def asset_one():
        raise Exception("foo")

    @asset
    def never_runs_asset(asset_one):
        return asset_one

    asset_job = build_assets_job("asset_job", [asset_one, never_runs_asset])

    with instance_for_test() as instance:
        # test with only one asset selected
        result = asset_job.execute_in_process(
            instance=instance, raise_on_error=False, op_selection=["asset_one"]
        )
        run_id = result.run_id

        assert instance.run_ids_for_asset_key(AssetKey("asset_one")) == [run_id]
        assert instance.run_ids_for_asset_key(AssetKey("never_runs_asset")) == []

    with instance_for_test() as instance:  # fresh event log storage
        # test with both assets selected
        result = asset_job.execute_in_process(instance=instance, raise_on_error=False)
        run_id = result.run_id

        assert instance.run_ids_for_asset_key(AssetKey("asset_one")) == [run_id]
        assert instance.run_ids_for_asset_key(AssetKey("never_runs_asset")) == [run_id]


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
            "my_out_name": Out(asset_key=AssetKey("my_asset_name")),
            "my_other_out_name": Out(asset_key=AssetKey("my_other_asset")),
        }
    )
    def my_asset():
        yield Output(1, "my_out_name")
        yield Output(2, "my_other_out_name")

    assets_job = build_assets_job("assets_job", [my_asset])

    with instance_for_test() as instance:
        result = assets_job.execute_in_process(instance=instance)
        records = instance.get_event_records(
            EventRecordsFilter(
                DagsterEventType.ASSET_MATERIALIZATION_PLANNED,
                AssetKey("my_asset_name"),
            )
        )
        assert result.run_id == records[0].event_log_entry.run_id
        run_id = result.run_id

        assert instance.run_ids_for_asset_key(AssetKey("my_asset_name")) == [run_id]
        assert instance.run_ids_for_asset_key(AssetKey("my_other_asset")) == [run_id]
