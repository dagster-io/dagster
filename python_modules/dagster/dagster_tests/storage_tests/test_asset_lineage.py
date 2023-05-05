import pytest
from dagster import AssetKey, DynamicOut, DynamicOutput, Out, Output, job, op
from dagster._core.definitions.events import AssetLineageInfo


def n_asset_keys(path, n):
    return AssetLineageInfo(AssetKey(path), set([str(i) for i in range(n)]))


def check_materialization(materialization, asset_key, parent_assets=None, metadata=None):
    event_data = materialization.event_specific_data
    assert event_data.materialization.asset_key == asset_key
    assert sorted(event_data.materialization.metadata) == sorted(metadata or {})
    assert event_data.asset_lineage == (parent_assets or [])


@pytest.mark.skip(reason="no longer supporting dynamic output asset keys")
def test_dynamic_output_definition_single_partition_materialization():
    @op(out={"output1": Out(asset_key=AssetKey("table1"))})
    def op1(_):
        return Output(None, "output1", metadata={"nrows": 123})

    @op(out={"output2": DynamicOut(asset_key=lambda context: AssetKey(context.mapping_key))})
    def op2(_, _input1):
        for i in range(4):
            yield DynamicOutput(
                7,
                mapping_key=str(i),
                output_name="output2",
                metadata={"some value": 3.21},
            )

    @op
    def do_nothing(_, _input1):
        pass

    @job
    def my_job():
        op2(op1()).map(do_nothing)

    result = my_job.execute_in_process()
    materializations = result.filter_events(lambda evt: evt.is_step_materialization)

    assert len(materializations) == 5

    check_materialization(materializations[0], AssetKey(["table1"]), metadata={"nrows": 123})
    seen_paths = set()
    for i in range(1, 5):
        path = materializations[i].asset_key.path
        seen_paths.add(tuple(path))
        check_materialization(
            materializations[i],
            AssetKey(path),
            metadata={"some value": 3.21},
            parent_assets=[AssetLineageInfo(AssetKey(["table1"]))],
        )
    assert len(seen_paths) == 4
