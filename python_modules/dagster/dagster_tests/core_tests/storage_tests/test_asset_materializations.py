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
from dagster.check import CheckError
from dagster.core.definitions.events import (
    AssetLineageInfo,
    EventMetadataEntry,
    PartitionMetadataEntry,
)
from dagster.core.errors import DagsterInvariantViolationError
from dagster.core.storage.io_manager import IOManager


def n_asset_keys(path, n):
    return AssetLineageInfo(AssetKey(path), set([str(i) for i in range(n)]))


def check_materialization(materialization, asset_key, parent_assets=None, metadata_entries=None):
    event_data = materialization.event_specific_data
    assert event_data.materialization.asset_key == asset_key
    assert sorted(event_data.materialization.metadata_entries) == sorted(metadata_entries or [])
    assert event_data.asset_lineage == (parent_assets or [])


def test_output_definition_single_partition_materialization():

    entry1 = EventMetadataEntry.int(123, "nrows")
    entry2 = EventMetadataEntry.float(3.21, "some value")

    @solid(output_defs=[OutputDefinition(name="output1", asset_key=AssetKey("table1"))])
    def solid1(_):
        return Output(None, "output1", metadata_entries=[entry1])

    @solid(output_defs=[OutputDefinition(name="output2", asset_key=lambda _: AssetKey("table2"))])
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
    assert len(materializations) == 2

    check_materialization(materializations[0], AssetKey(["table1"]), metadata_entries=[entry1])
    check_materialization(
        materializations[1],
        AssetKey(["table2"]),
        metadata_entries=[entry2],
        parent_assets=[AssetLineageInfo(AssetKey(["table1"]))],
    )


def test_output_definition_multiple_partition_materialization():

    entry1 = EventMetadataEntry.int(123, "nrows")
    entry2 = EventMetadataEntry.float(3.21, "some value")

    partition_entries = [EventMetadataEntry.int(123 * i * i, "partition count") for i in range(3)]

    @solid(
        output_defs=[
            OutputDefinition(
                name="output1", asset_key=AssetKey("table1"), asset_partitions=set(["0", "1", "2"])
            )
        ]
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

    @solid(output_defs=[OutputDefinition(name="output2", asset_key=AssetKey("table2"))])
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
        metadata_entries=[entry2],
        parent_assets=[n_asset_keys("table1", 3)],
    )


def test_io_manager_single_partition_materialization():

    entry1 = EventMetadataEntry.int(123, "nrows")
    entry2 = EventMetadataEntry.float(3.21, "some value")

    class MyIOManager(IOManager):
        def handle_output(self, context, obj):
            # store asset
            yield entry1

        def load_input(self, context):
            return None

        def get_output_asset_key(self, context):
            return AssetKey([context.step_key])

    @io_manager
    def my_io_manager(_):
        return MyIOManager()

    @solid(output_defs=[OutputDefinition(name="output1")])
    def solid1(_):
        return Output(None, "output1")

    @solid(output_defs=[OutputDefinition(name="output2")])
    def solid2(_, _input1):
        yield Output(
            7,
            "output2",
            metadata_entries=[entry2],
        )

    @pipeline(mode_defs=[ModeDefinition(resource_defs={"io_manager": my_io_manager})])
    def my_pipeline():
        solid2(solid1())

    result = execute_pipeline(my_pipeline)
    events = result.step_event_list
    materializations = [
        event for event in events if event.event_type_value == "ASSET_MATERIALIZATION"
    ]
    assert len(materializations) == 2

    check_materialization(materializations[0], AssetKey(["solid1"]), metadata_entries=[entry1])
    check_materialization(
        materializations[1],
        AssetKey(["solid2"]),
        metadata_entries=[entry1, entry2],
        parent_assets=[AssetLineageInfo(AssetKey(["solid1"]))],
    )


def test_partition_specific_fails_on_na_partitions():
    @solid(
        output_defs=[OutputDefinition(asset_key=AssetKey("key"), asset_partitions=set(["1", "2"]))]
    )
    def fail_solid(_):
        yield Output(
            None,
            metadata_entries=[PartitionMetadataEntry("3", EventMetadataEntry.int(1, "x"))],
        )

    @pipeline
    def my_pipeline():
        fail_solid()

    with pytest.raises(DagsterInvariantViolationError):
        execute_pipeline(my_pipeline)


def test_partition_specific_fails_on_zero_partitions():
    @solid(output_defs=[OutputDefinition(asset_key=AssetKey("key"))])
    def fail_solid(_):
        yield Output(
            None,
            metadata_entries=[PartitionMetadataEntry("3", EventMetadataEntry.int(1, "x"))],
        )

    @pipeline
    def my_pipeline():
        fail_solid()

    with pytest.raises(DagsterInvariantViolationError):
        execute_pipeline(my_pipeline)


def test_fail_fast_with_nonesense_metadata():
    @solid(output_defs=[OutputDefinition(asset_key=AssetKey("key"))])
    def fail_solid(_):
        yield Output(
            None,
            metadata_entries=["some_string_I_think_is_metadata"],
        )

    @pipeline
    def my_pipeline():
        fail_solid()

    with pytest.raises(CheckError):
        execute_pipeline(my_pipeline)


def test_def_only_asset_partitions_fails():

    with pytest.raises(CheckError):

        OutputDefinition(asset_partitions=set(["1"]))

    with pytest.raises(CheckError):

        InputDefinition("name", asset_partitions=set(["1"]))
