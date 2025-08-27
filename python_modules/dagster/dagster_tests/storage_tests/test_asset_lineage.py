import dagster as dg
import pytest
from dagster._core.definitions.events import AssetLineageInfo


def n_asset_keys(path, n):
    return AssetLineageInfo(dg.AssetKey(path), set([str(i) for i in range(n)]))


def check_materialization(materialization, asset_key, parent_assets=None, metadata=None):
    event_data = materialization.event_specific_data
    assert event_data.materialization.asset_key == asset_key
    assert sorted(event_data.materialization.metadata) == sorted(metadata or {})
    assert event_data.asset_lineage == (parent_assets or [])


@pytest.mark.skip(reason="no longer supporting dynamic output asset keys")
def test_dynamic_output_definition_single_partition_materialization():
    @dg.op(out={"output1": dg.Out(asset_key=dg.AssetKey("table1"))})  # pyright: ignore[reportCallIssue]
    def op1(_):
        return dg.Output(None, "output1", metadata={"nrows": 123})

    @dg.op(
        out={"output2": dg.DynamicOut(asset_key=lambda context: dg.AssetKey(context.mapping_key))}  # pyright: ignore[reportCallIssue]
    )
    def op2(_, _input1):
        for i in range(4):
            yield dg.DynamicOutput(
                7,
                mapping_key=str(i),
                output_name="output2",
                metadata={"some value": 3.21},
            )

    @dg.op
    def do_nothing(_, _input1):
        pass

    @dg.job
    def my_job():
        op2(op1()).map(do_nothing)

    result = my_job.execute_in_process()
    materializations = result.filter_events(lambda evt: evt.is_step_materialization)

    assert len(materializations) == 5

    check_materialization(materializations[0], dg.AssetKey(["table1"]), metadata={"nrows": 123})
    seen_paths = set()
    for i in range(1, 5):
        path = materializations[i].asset_key.path  # pyright: ignore[reportOptionalMemberAccess]
        seen_paths.add(tuple(path))
        check_materialization(
            materializations[i],
            dg.AssetKey(path),
            metadata={"some value": 3.21},
            parent_assets=[AssetLineageInfo(dg.AssetKey(["table1"]))],
        )
    assert len(seen_paths) == 4
