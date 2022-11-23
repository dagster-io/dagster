import pytest

from dagster import (
    AssetKey,
    AssetObservation,
    In,
    Out,
    Output,
    StaticPartitionsDefinition,
    asset,
    build_input_context,
    io_manager,
    job,
    op,
    root_input_manager,
)
from dagster._check import CheckError
from dagster._core.definitions.events import AssetLineageInfo
from dagster._core.definitions.metadata import MetadataEntry, PartitionMetadataEntry
from dagster._core.errors import DagsterInvariantViolationError
from dagster._core.storage.io_manager import IOManager
from dagster._legacy import InputDefinition, OutputDefinition, build_assets_job


def n_asset_keys(path, n):
    return AssetLineageInfo(AssetKey(path), set([str(i) for i in range(n)]))


def check_materialization(materialization, asset_key, parent_assets=None, metadata_entries=None):
    event_data = materialization.event_specific_data
    assert event_data.materialization.asset_key == asset_key
    assert sorted(event_data.materialization.metadata_entries) == sorted(metadata_entries or [])
    assert event_data.asset_lineage == (parent_assets or [])


@pytest.mark.skip(reason="no longer supporting dynamic asset key")
def test_output_definition_single_partition_materialization():

    entry1 = MetadataEntry("nrows", value=123)
    entry2 = MetadataEntry("some value", value=3.21)

    @op(out={"output1": Out(asset_key=AssetKey("table1"))})
    def op1(_):
        return Output(None, "output1", metadata_entries=[entry1])

    @op(out={"output2": Out(asset_key=lambda _: AssetKey("table2"))})
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
    events = result.filter_events(lambda evt: evt.is_step_event)
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

    entry1 = MetadataEntry("nrows", value=123)
    entry2 = MetadataEntry("some value", value=3.21)

    partition_entries = [MetadataEntry("partition count", value=123 * i * i) for i in range(3)]

    @op(
        out={
            "output1": Out(
                asset_key=AssetKey("table1"),
                asset_partitions=set(["0", "1", "2"]),
            )
        }
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

    @op(out={"output2": Out(asset_key=AssetKey("table2"))})
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
    events = result.filter_events(lambda evt: evt.is_step_event)
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


def test_io_manager_add_input_metadata():
    class MyIOManager(IOManager):
        def handle_output(self, context, obj):
            pass

        def load_input(self, context):
            context.add_input_metadata(metadata={"foo": "bar"})
            context.add_input_metadata(metadata={"baz": "qux"})

            observations = context.get_observations()
            assert observations[0].asset_key == context.asset_key
            assert observations[0].metadata_entries[0].label == "foo"
            assert observations[1].metadata_entries[0].label == "baz"
            return 1

    @io_manager
    def my_io_manager(_):
        return MyIOManager()

    in_asset_key = AssetKey(["a", "b"])
    out_asset_key = AssetKey(["c", "d"])

    @op(out=Out(asset_key=out_asset_key))
    def before():
        pass

    @op(ins={"a": In(asset_key=in_asset_key)}, out={})
    def after(a):
        del a

    @job(resource_defs={"io_manager": my_io_manager})
    def my_job():
        after(before())

    get_observation = lambda event: event.event_specific_data.asset_observation

    result = my_job.execute_in_process()
    observations = [
        event for event in result.all_node_events if event.event_type_value == "ASSET_OBSERVATION"
    ]

    # first observation
    assert observations[0].step_key == "after"
    assert get_observation(observations[0]) == AssetObservation(
        asset_key=in_asset_key, metadata={"foo": "bar"}
    )
    # second observation
    assert observations[1].step_key == "after"
    assert get_observation(observations[1]) == AssetObservation(
        asset_key=in_asset_key, metadata={"baz": "qux"}
    )

    # confirm loaded_input event contains metadata
    loaded_input_event = [
        event for event in result.all_events if event.event_type_value == "LOADED_INPUT"
    ][0]
    assert loaded_input_event
    loaded_input_event_metadata = loaded_input_event.event_specific_data.metadata_entries
    assert len(loaded_input_event_metadata) == 2
    assert loaded_input_event_metadata[0].label == "foo"
    assert loaded_input_event_metadata[1].label == "baz"


def test_root_input_manager_add_input_metadata():
    @root_input_manager
    def my_root_input_manager(context):
        context.add_input_metadata(metadata={"foo": "bar"})
        context.add_input_metadata(metadata={"baz": "qux"})
        return []

    @op(ins={"input1": In(root_manager_key="my_root_input_manager")})
    def my_op(_, input1):
        return input1

    @job(resource_defs={"my_root_input_manager": my_root_input_manager})
    def my_job():
        my_op()

    result = my_job.execute_in_process()
    loaded_input_event = [
        event for event in result.all_events if event.event_type_value == "LOADED_INPUT"
    ][0]
    metadata_entries = loaded_input_event.event_specific_data.metadata_entries
    assert len(metadata_entries) == 2
    assert metadata_entries[0].label == "foo"
    assert metadata_entries[1].label == "baz"


def test_io_manager_single_partition_add_input_metadata():
    partitions_def = StaticPartitionsDefinition(["a", "b", "c"])

    @asset(partitions_def=partitions_def)
    def asset_1():
        return 1

    @asset(partitions_def=partitions_def)
    def asset_2(asset_1):
        return asset_1 + 1

    class MyIOManager(IOManager):
        def handle_output(self, context, obj):
            pass

        def load_input(self, context):
            context.add_input_metadata(metadata={"foo": "bar"}, description="hello world")
            return 1

    @io_manager
    def my_io_manager(_):
        return MyIOManager()

    assets_job = build_assets_job(
        "assets_job", [asset_1, asset_2], resource_defs={"io_manager": my_io_manager}
    )
    result = assets_job.execute_in_process(partition_key="a")

    get_observation = lambda event: event.event_specific_data.asset_observation

    observations = [
        event for event in result.all_node_events if event.event_type_value == "ASSET_OBSERVATION"
    ]

    assert observations[0].step_key == "asset_2"
    assert get_observation(observations[0]) == AssetObservation(
        asset_key="asset_1",
        metadata={"foo": "bar"},
        description="hello world",
        partition="a",
    )


def test_build_input_context_add_input_metadata():
    @op
    def my_op():
        pass

    context = build_input_context(op_def=my_op)
    context.add_input_metadata({"foo": "bar"})


def test_io_manager_single_partition_materialization():

    entry1 = MetadataEntry("nrows", value=123)
    entry2 = MetadataEntry("some value", value=3.21)

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

    @op(out={"output1": Out()})
    def op1(_):
        return Output(None, "output1")

    @op(out={"output2": Out()})
    def op2(_, _input1):
        yield Output(
            7,
            "output2",
            metadata_entries=[entry2],
        )

    @job(resource_defs={"io_manager": my_io_manager})
    def my_job():
        op2(op1())

    result = my_job.execute_in_process()
    events = result.filter_events(lambda evt: evt.is_step_event)
    materializations = [
        event for event in events if event.event_type_value == "ASSET_MATERIALIZATION"
    ]
    assert len(materializations) == 2

    check_materialization(materializations[0], AssetKey(["op1"]), metadata_entries=[entry1])
    check_materialization(
        materializations[1],
        AssetKey(["op2"]),
        metadata_entries=[entry1, entry2],
        parent_assets=[AssetLineageInfo(AssetKey(["op1"]))],
    )


def test_partition_specific_fails_on_na_partitions():
    @op(out=Out(asset_key=AssetKey("key"), asset_partitions=set(["1", "2"])))
    def fail_op(_):
        yield Output(
            None,
            metadata_entries=[PartitionMetadataEntry("3", MetadataEntry("x", value=1))],
        )

    @job
    def my_job():
        fail_op()

    with pytest.raises(DagsterInvariantViolationError):
        my_job.execute_in_process()


def test_partition_specific_fails_on_zero_partitions():
    @op(out=Out(asset_key=AssetKey("key")))
    def fail_op(_):
        yield Output(
            None,
            metadata_entries=[PartitionMetadataEntry("3", MetadataEntry("x", value=1))],
        )

    @job
    def my_job():
        fail_op()

    with pytest.raises(DagsterInvariantViolationError):
        my_job.execute_in_process()


def test_fail_fast_with_nonesense_metadata():
    @op(out=Out(asset_key=AssetKey("key")))
    def fail_op(_):
        yield Output(
            None,
            metadata_entries=["some_string_I_think_is_metadata"],
        )

    @job
    def my_job():
        fail_op()

    with pytest.raises(CheckError):
        my_job.execute_in_process()


def test_def_only_asset_partitions_fails():

    with pytest.raises(CheckError):

        OutputDefinition(asset_partitions=set(["1"]))

    with pytest.raises(CheckError):

        InputDefinition("name", asset_partitions=set(["1"]))
