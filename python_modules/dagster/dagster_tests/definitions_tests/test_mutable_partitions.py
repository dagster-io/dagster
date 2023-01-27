import pytest
from dagster import (
    DagsterInstance,
    IOManager,
    MutablePartitionsDefinition,
    asset,
    materialize_to_memory,
)


def test_single_asset():
    @asset(partitions_def=MutablePartitionsDefinition(name="fruits"))
    def asset1(context):
        assert context.partition_key == "apple"
        assert context.asset_key_for_output() == "apple"
        assert context.asset_keys_for_output() == ["apple"]

    instance = DagsterInstance.ephemeral()
    with pytest.raises():
        materialize_to_memory([asset1], instance=instance, partition_key="apple")

    instance.add_partition(partitions_def_name="fruits", partition_key="apple")
    materialize_to_memory([asset1], instance=instance, partition_key="apple")


def test_asset_dep():
    partitions_def = MutablePartitionsDefinition(name="fruits")

    @asset(partitions_def=partitions_def)
    def asset1():
        ...

    @asset(partitions_def=partitions_def, non_argument_deps={"asset1"})
    def asset2(context):
        assert context.partition_key == "apple"
        assert context.asset_key_for_output() == "apple"
        assert context.asset_keys_for_output() == ["apple"]
        assert context.asset_key_for_input() == "apple"
        assert context.asset_keys_for_input() == ["apple"]

    instance = DagsterInstance.ephemeral()

    instance.add_partition(partitions_def_name="fruits", partition_key="apple")
    materialize_to_memory([asset1], instance=instance, partition_key="apple")


def test_io_manager_context():
    partitions_def = MutablePartitionsDefinition(name="fruits")

    class MyIOManager(IOManager):
        def handle_output(self, context, obj):
            assert context.partition_key == "apple"
            assert context.asset_partition_key == "apple"
            assert context.asset_partition_keys == ["apple"]

        def load_input(self, context):
            assert context.partition_key == "apple"
            assert context.asset_partition_key == "apple"
            assert context.asset_partition_keys == ["apple"]

    @asset(partitions_def=partitions_def)
    def asset1():
        ...

    @asset(partitions_def=partitions_def, non_argument_deps={"asset1"})
    def asset2(context):
        ...

    instance = DagsterInstance.ephemeral()

    instance.add_partition(partitions_def_name="fruits", partition_key="apple")
    materialize_to_memory(
        [asset1], instance=instance, partition_key="apple", resources={"io_manager": MyIOManager()}
    )
