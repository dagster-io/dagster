import pytest
from dagster import (
    AssetKey,
    DagsterUnknownPartitionError,
    IOManager,
    asset,
    materialize,
    materialize_to_memory,
)
from dagster._check import CheckError
from dagster._core.definitions.mutable_partitions_definition import MutablePartitionsDefinition
from dagster._core.test_utils import instance_for_test


def test_mutable_partitions_def_methods():
    foo = MutablePartitionsDefinition("foo")
    with instance_for_test() as instance:
        foo.add_partitions(["a", "b"], instance=instance)
        assert set([p.name for p in foo.get_partitions(mutable_partitions_store=instance)]) == {
            "a",
            "b",
        }
        assert foo.has_partition("a", instance=instance)

        foo.delete_partition("a", instance=instance)
        assert set([p.name for p in foo.get_partitions(mutable_partitions_store=instance)]) == {"b"}
        assert foo.has_partition("a", instance=instance) is False


def test_mutable_partitioned_run():
    with instance_for_test() as instance:
        partitions_def = MutablePartitionsDefinition("foo")

        @asset(partitions_def=partitions_def)
        def my_asset():
            return 1

        with pytest.raises(DagsterUnknownPartitionError):
            materialize([my_asset], instance=instance, partition_key="a")

        partitions_def.add_partitions(["a"], instance)
        assert partitions_def.get_partition_keys(mutable_partitions_store=instance) == ["a"]
        assert materialize([my_asset], instance=instance, partition_key="a").success
        materialization = instance.get_latest_materialization_event(AssetKey("my_asset"))
        assert materialization
        assert materialization.dagster_event.partition == "a"

        with pytest.raises(CheckError):
            partitions_def.get_partition_keys()


def test_mutable_partitioned_asset_dep():
    partitions_def = MutablePartitionsDefinition(name="fruits")

    @asset(partitions_def=partitions_def)
    def asset1():
        pass

    @asset(partitions_def=partitions_def, non_argument_deps={"asset1"})
    def asset2(context):
        assert context.partition_key == "apple"
        assert context.asset_key_for_output() == "apple"
        assert context.asset_keys_for_output() == ["apple"]
        assert context.asset_key_for_input() == "apple"
        assert context.asset_keys_for_input() == ["apple"]

    with instance_for_test() as instance:
        partitions_def.add_partitions(["apple"], instance=instance)
        materialize_to_memory([asset1], instance=instance, partition_key="apple")


def test_mutable_partitioned_asset_io_manager_context():
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

    @asset(partitions_def=partitions_def, io_manager_key="custom_io")
    def asset1():
        return 1

    @asset(
        partitions_def=partitions_def,
        io_manager_key="custom_io",
    )
    def asset2(context, asset1):
        return asset1

    with instance_for_test() as instance:
        partitions_def.add_partitions(["apple"], instance=instance)

        materialize(
            [asset1, asset2],
            instance=instance,
            partition_key="apple",
            resources={"custom_io": MyIOManager()},
        )


def test_mutable_partitions_no_instance_provided():
    partitions_def = MutablePartitionsDefinition(name="fruits")

    with pytest.raises(CheckError, match="provide a dagster instance"):
        partitions_def.get_partitions()


def test_mutable_partitions_mapping():
    partitions_def = MutablePartitionsDefinition(name="fruits")

    @asset(partitions_def=partitions_def)
    def mutable1(context):
        assert context.asset_partition_key_for_output() == "apple"
        return 1

    @asset(partitions_def=partitions_def)
    def mutable2(context, mutable1):
        assert context.asset_partition_keys_for_input("mutable1") == ["apple"]
        assert context.asset_partition_key_for_output() == "apple"
        return 1

    @asset
    def unpartitioned(context, mutable1):
        assert context.asset_partition_keys_for_input("mutable1") == ["apple"]
        return 1

    with instance_for_test() as instance:
        partitions_def.add_partitions(["apple"], instance=instance)

        materialize([mutable1, mutable2, unpartitioned], instance=instance, partition_key="apple")


def test_unpartitioned_downstream_of_mutable_asset():
    partitions = [
        "apple",
        "banana",
        "cantaloupe",
    ]

    partitions_def = MutablePartitionsDefinition(name="fruits")

    @asset(partitions_def=partitions_def)
    def mutable1(context):
        return 1

    @asset
    def unpartitioned(context, mutable1):
        assert set(context.asset_partition_keys_for_input("mutable1")) == set(partitions)
        return 1

    with instance_for_test() as instance:
        partitions_def.add_partitions(partitions, instance=instance)

        for partition in partitions[:-1]:
            materialize([mutable1], instance=instance, partition_key=partition)

        materialize([unpartitioned, mutable1], instance=instance, partition_key=partitions[-1])
