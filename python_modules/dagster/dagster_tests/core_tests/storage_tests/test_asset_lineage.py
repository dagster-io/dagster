import pytest
from dagster import (
    AssetKey,
    InputDefinition,
    ModeDefinition,
    Output,
    OutputDefinition,
    execute_pipeline,
    io_manager,
    pipeline,
    solid,
)
from dagster.core.definitions.events import (
    AssetLineageInfo,
    EventMetadataEntry,
    PartitionMetadataEntry,
)
from dagster.core.errors import DagsterInvariantViolationError
from dagster.core.storage.io_manager import IOManager
from dagster.experimental import DynamicOutput, DynamicOutputDefinition


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

    @solid(
        output_defs=[
            OutputDefinition(name="outputA", io_manager_key="asset_io_manager"),
            OutputDefinition(name="outputB", io_manager_key="asset_io_manager"),
        ]
    )
    def solid_produce(_):
        yield Output(None, "outputA")
        yield Output(None, "outputB")

    @solid(output_defs=[OutputDefinition(name="outputT", io_manager_key="asset_io_manager")])
    def solid_transform(_, _input):
        return None

    @solid(output_defs=[OutputDefinition(name="outputC", io_manager_key="asset_io_manager")])
    def solid_combine(_, _inputA, _inputB):
        return Output(None, "outputC")

    @pipeline(mode_defs=[ModeDefinition(resource_defs={"asset_io_manager": my_io_manager})])
    def my_pipeline():
        a, b = solid_produce()
        at = solid_transform.alias("a_transform")(a)
        bt = solid_transform.alias("b_transform")(b)
        solid_combine(at, bt)

    result = execute_pipeline(my_pipeline)
    events = result.step_event_list
    materializations = [
        event for event in events if event.event_type_value == "ASSET_MATERIALIZATION"
    ]
    assert len(materializations) == 5

    check_materialization(materializations[0], AssetKey(["solid_produce", "outputA"]))
    check_materialization(materializations[1], AssetKey(["solid_produce", "outputB"]))
    check_materialization(
        materializations[-1],
        AssetKey(
            ["solid_combine", "outputC"],
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

    @solid(
        output_defs=[
            OutputDefinition(asset_key=AssetKey("x"), io_manager_key="asset_io_manager"),
        ]
    )
    def fail_solid(_):
        return 1

    @pipeline(mode_defs=[ModeDefinition(resource_defs={"asset_io_manager": my_io_manager})])
    def my_pipeline():
        fail_solid()

    with pytest.raises(DagsterInvariantViolationError):
        execute_pipeline(my_pipeline)


def test_input_definition_multiple_partition_lineage():

    entry1 = EventMetadataEntry.int(123, "nrows")
    entry2 = EventMetadataEntry.float(3.21, "some value")

    partition_entries = [EventMetadataEntry.int(123 * i * i, "partition count") for i in range(3)]

    @solid(
        output_defs=[
            OutputDefinition(
                name="output1",
                asset_key=AssetKey("table1"),
                asset_partitions=set([str(i) for i in range(3)]),
            )
        ],
    )
    def solid1(_):
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

    @solid(
        input_defs=[
            # here, only take 1 of the asset keys specified by the output
            InputDefinition(
                name="_input1", asset_key=AssetKey("table1"), asset_partitions=set(["0"])
            )
        ],
        output_defs=[OutputDefinition(name="output2", asset_key=lambda _: AssetKey("table2"))],
    )
    def solid2(_, _input1):
        yield Output(
            7,
            "output2",
            metadata_entries=[entry2],
        )

    @pipeline
    def my_pipeline():
        solid2(solid1())

    result = execute_pipeline(my_pipeline)
    events = result.step_event_list
    materializations = [
        event for event in events if event.event_type_value == "ASSET_MATERIALIZATION"
    ]
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

    @solid(output_defs=[OutputDefinition(io_manager_key="asset_io_manager")])
    def io_manager_solid(_):
        return 1

    @solid(
        output_defs=[OutputDefinition(asset_key=AssetKey(["output_def_table", "output_def_solid"]))]
    )
    def output_def_solid(_):
        return 1

    @solid(
        output_defs=[
            OutputDefinition(name="a", asset_key=AssetKey(["output_def_table", "combine_solid"])),
            OutputDefinition(name="b", io_manager_key="asset_io_manager"),
        ]
    )
    def combine_solid(_, _a, _b):
        yield Output(None, "a")
        yield Output(None, "b")

    @pipeline(mode_defs=[ModeDefinition(resource_defs={"asset_io_manager": my_io_manager})])
    def my_pipeline():
        a = io_manager_solid()
        b = output_def_solid()
        combine_solid(a, b)

    result = execute_pipeline(my_pipeline)
    events = result.step_event_list
    materializations = [
        event for event in events if event.event_type_value == "ASSET_MATERIALIZATION"
    ]
    assert len(materializations) == 4

    check_materialization(materializations[0], AssetKey(["io_manager_table", "io_manager_solid"]))
    check_materialization(materializations[1], AssetKey(["output_def_table", "output_def_solid"]))
    check_materialization(
        materializations[2],
        AssetKey(["output_def_table", "combine_solid"]),
        parent_assets=[
            AssetLineageInfo(AssetKey(["io_manager_table", "io_manager_solid"])),
            AssetLineageInfo(AssetKey(["output_def_table", "output_def_solid"])),
        ],
    )
    check_materialization(
        materializations[3],
        AssetKey(["io_manager_table", "combine_solid"]),
        parent_assets=[
            AssetLineageInfo(AssetKey(["io_manager_table", "io_manager_solid"])),
            AssetLineageInfo(AssetKey(["output_def_table", "output_def_solid"])),
        ],
    )


def test_dynamic_output_definition_single_partition_materialization():

    entry1 = EventMetadataEntry.int(123, "nrows")
    entry2 = EventMetadataEntry.float(3.21, "some value")

    @solid(output_defs=[OutputDefinition(name="output1", asset_key=AssetKey("table1"))])
    def solid1(_):
        return Output(None, "output1", metadata_entries=[entry1])

    @solid(
        output_defs=[
            DynamicOutputDefinition(
                name="output2", asset_key=lambda context: AssetKey(context.mapping_key)
            )
        ]
    )
    def solid2(_, _input1):
        for i in range(4):
            yield DynamicOutput(
                7,
                mapping_key=str(i),
                output_name="output2",
                metadata_entries=[entry2],
            )

    @solid
    def do_nothing(_, _input1):
        pass

    @pipeline
    def my_pipeline():
        solid2(solid1()).map(do_nothing)

    result = execute_pipeline(my_pipeline)
    events = result.step_event_list
    materializations = [
        event for event in events if event.event_type_value == "ASSET_MATERIALIZATION"
    ]
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
