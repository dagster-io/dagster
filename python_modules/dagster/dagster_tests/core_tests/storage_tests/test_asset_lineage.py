import pytest

from dagster import AssetKey, DynamicOut, DynamicOutput, In, Out, Output, io_manager, job, op
from dagster._core.definitions.events import AssetLineageInfo
from dagster._core.definitions.metadata import MetadataEntry, PartitionMetadataEntry
from dagster._core.errors import DagsterInvariantViolationError
from dagster._core.storage.io_manager import IOManager


def n_asset_keys(path, n):
    return AssetLineageInfo(AssetKey(path), set([str(i) for i in range(n)]))


def check_materialization(materialization, asset_key, parent_assets=None, metadata_entries=None):
    event_data = materialization.event_specific_data
    assert event_data.materialization.asset_key == asset_key
    assert sorted(event_data.materialization.metadata_entries) == sorted(metadata_entries or [])
    assert event_data.asset_lineage == (parent_assets or [])


def test_io_manager_diamond_lineage():
    class MyIOManager(IOManager):
        def handle_output(self, context, obj):
            # store asset
            return

        def load_input(self, context):
            return None

        def get_output_asset_key(self, context):
            return AssetKey([context.step_key, context.name])

    @io_manager
    def my_io_manager(_):
        return MyIOManager()

    @op(
        out={
            "outputA": Out(io_manager_key="asset_io_manager"),
            "outputB": Out(io_manager_key="asset_io_manager"),
        }
    )
    def op_produce(_):
        yield Output(None, "outputA")
        yield Output(None, "outputB")

    @op(out={"outputT": Out(io_manager_key="asset_io_manager")})
    def op_transform(_, _input):
        return None

    @op(out={"outputC": Out(io_manager_key="asset_io_manager")})
    def op_combine(_, _inputA, _inputB):
        return Output(None, "outputC")

    @job(resource_defs={"asset_io_manager": my_io_manager})
    def my_job():
        a, b = op_produce()
        at = op_transform.alias("a_transform")(a)
        bt = op_transform.alias("b_transform")(b)
        op_combine(at, bt)

    result = my_job.execute_in_process()
    materializations = result.get_asset_materialization_events()
    assert len(materializations) == 5

    check_materialization(materializations[0], AssetKey(["op_produce", "outputA"]))
    check_materialization(materializations[1], AssetKey(["op_produce", "outputB"]))
    check_materialization(
        materializations[-1],
        AssetKey(
            ["op_combine", "outputC"],
        ),
        parent_assets=[
            AssetLineageInfo(AssetKey(["a_transform", "outputT"])),
            AssetLineageInfo(AssetKey(["b_transform", "outputT"])),
        ],
    )


def test_multiple_definition_fails():
    class MyIOManager(IOManager):
        def handle_output(self, context, obj):
            # store asset
            return

        def load_input(self, context):
            return None

        def get_output_asset_key(self, context):
            return AssetKey([context.step_key, context.name])

    @io_manager
    def my_io_manager(_):
        return MyIOManager()

    @op(out=Out(asset_key=AssetKey("x"), io_manager_key="asset_io_manager"))
    def fail_op(_):
        return 1

    @job(resource_defs={"asset_io_manager": my_io_manager})
    def my_job():
        fail_op()

    with pytest.raises(DagsterInvariantViolationError):
        my_job.execute_in_process()


@pytest.mark.skip(reason="no longer supporting lineage feature")
def test_input_definition_multiple_partition_lineage():

    entry1 = MetadataEntry("nrows", value=123)
    entry2 = MetadataEntry("some value", value=3.21)

    partition_entries = [MetadataEntry("partition count", value=123 * i * i) for i in range(3)]

    @op(
        out={
            "output1": Out(
                asset_key=AssetKey("table1"),
                asset_partitions=set([str(i) for i in range(3)]),
            )
        },
    )
    def op1(_):
        return Output(
            None,
            "output1",
            metadata_entries=[
                entry1,
                *[
                    PartitionMetadataEntry(str(i), entry)
                    for i, entry in enumerate(partition_entries)
                ],
            ],
        )

    @op(
        ins={
            "_input1": In(
                asset_key=AssetKey("table1"),
                asset_partitions=set(["0"]),
            )
        },
        out={"output2": Out(asset_key=lambda _: AssetKey("table2"))},
    )
    def op2(_, _input1):
        yield Output(
            7,
            "output2",
            metadata_entries=[entry2],
        )

    @job
    def my_job():
        op2(op1())

    result = my_job.execute_in_process()
    materializations = result.get_asset_materialization_events()

    assert len(materializations) == 4

    seen_partitions = set()
    for i in range(3):
        partition = materializations[i].partition
        seen_partitions.add(partition)
        check_materialization(
            materializations[i],
            AssetKey(["table1"]),
            metadata_entries=[entry1, partition_entries[int(partition)]],
        )

    assert len(seen_partitions) == 3

    check_materialization(
        materializations[-1],
        AssetKey(["table2"]),
        parent_assets=[n_asset_keys("table1", 1)],
        metadata_entries=[entry2],
    )


def test_mixed_asset_definition_lineage():
    class MyIOManager(IOManager):
        def handle_output(self, context, obj):
            # store asset
            return

        def load_input(self, context):
            return None

        def get_output_asset_key(self, context):
            return AssetKey(["io_manager_table", context.step_key])

    @io_manager
    def my_io_manager(_):
        return MyIOManager()

    @op(out=Out(io_manager_key="asset_io_manager"))
    def io_manager_op(_):
        return 1

    @op(out=Out(asset_key=AssetKey(["output_def_table", "output_def_op"])))
    def output_def_op(_):
        return 1

    @op(
        out={
            "a": Out(asset_key=AssetKey(["output_def_table", "combine_op"])),
            "b": Out(io_manager_key="asset_io_manager"),
        }
    )
    def combine_op(_, _a, _b):
        yield Output(None, "a")
        yield Output(None, "b")

    @job(resource_defs={"asset_io_manager": my_io_manager})
    def my_job():
        a = io_manager_op()
        b = output_def_op()
        combine_op(a, b)

    result = my_job.execute_in_process()
    materializations = result.get_asset_materialization_events()

    assert len(materializations) == 4

    check_materialization(materializations[0], AssetKey(["io_manager_table", "io_manager_op"]))
    check_materialization(materializations[1], AssetKey(["output_def_table", "output_def_op"]))
    check_materialization(
        materializations[2],
        AssetKey(["output_def_table", "combine_op"]),
        parent_assets=[
            AssetLineageInfo(AssetKey(["io_manager_table", "io_manager_op"])),
            AssetLineageInfo(AssetKey(["output_def_table", "output_def_op"])),
        ],
    )
    check_materialization(
        materializations[3],
        AssetKey(["io_manager_table", "combine_op"]),
        parent_assets=[
            AssetLineageInfo(AssetKey(["io_manager_table", "io_manager_op"])),
            AssetLineageInfo(AssetKey(["output_def_table", "output_def_op"])),
        ],
    )


@pytest.mark.skip(reason="no longer supporting dynamic output asset keys")
def test_dynamic_output_definition_single_partition_materialization():

    entry1 = MetadataEntry("nrows", value=123)
    entry2 = MetadataEntry("some value", value=3.21)

    @op(out={"output1": Out(asset_key=AssetKey("table1"))})
    def op1(_):
        return Output(None, "output1", metadata_entries=[entry1])

    @op(out={"output2": DynamicOut(asset_key=lambda context: AssetKey(context.mapping_key))})
    def op2(_, _input1):
        for i in range(4):
            yield DynamicOutput(
                7,
                mapping_key=str(i),
                output_name="output2",
                metadata_entries=[entry2],
            )

    @op
    def do_nothing(_, _input1):
        pass

    @job
    def my_job():
        op2(op1()).map(do_nothing)

    result = my_job.execute_in_process()
    materializations = result.get_asset_materialization_events()

    assert len(materializations) == 5

    check_materialization(materializations[0], AssetKey(["table1"]), metadata_entries=[entry1])
    seen_paths = set()
    for i in range(1, 5):
        path = materializations[i].asset_key.path
        seen_paths.add(tuple(path))
        check_materialization(
            materializations[i],
            AssetKey(path),
            metadata_entries=[entry2],
            parent_assets=[AssetLineageInfo(AssetKey(["table1"]))],
        )
    assert len(seen_paths) == 4
