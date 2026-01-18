from collections.abc import Callable, Sequence
from datetime import datetime
from typing import Optional

import dagster as dg
import pytest
from dagster import AssetExecutionContext
from dagster._check import CheckError
from dagster._core.test_utils import get_paginated_partition_keys


@pytest.mark.parametrize(
    argnames=["partition_fn"],
    argvalues=[
        (lambda _current_time: [dg.Partition("a_partition")],),
        (lambda _current_time: [dg.Partition(x) for x in range(10)],),
    ],
)
def test_dynamic_partitions_partitions(
    partition_fn: Callable[[Optional[datetime]], Sequence[dg.Partition]],
):
    partitions = dg.DynamicPartitionsDefinition(partition_fn)

    all_keys = [p.name for p in partition_fn(None)]
    assert partitions.get_partition_keys() == all_keys
    assert get_paginated_partition_keys(partitions) == all_keys
    assert get_paginated_partition_keys(partitions, ascending=False) == list(reversed(all_keys))


@pytest.mark.parametrize(
    argnames=["partition_fn"],
    argvalues=[
        (lambda _current_time: ["a_partition"],),
        (lambda _current_time: [str(x) for x in range(10)],),
    ],
)
def test_dynamic_partitions_keys(partition_fn: Callable[[Optional[datetime]], Sequence[str]]):
    partitions = dg.DynamicPartitionsDefinition(partition_fn)

    all_keys = partition_fn(None)
    assert partitions.get_partition_keys() == all_keys
    assert get_paginated_partition_keys(partitions) == all_keys
    assert get_paginated_partition_keys(partitions, ascending=False) == list(reversed(all_keys))


def test_dynamic_partitions_def_methods():
    partitions = dg.DynamicPartitionsDefinition(name="foo")
    with dg.instance_for_test() as instance:
        instance.add_dynamic_partitions("foo", ["a", "b"])
        all_keys = ["a", "b"]
        assert partitions.get_partition_keys(dynamic_partitions_store=instance) == all_keys
        assert (
            get_paginated_partition_keys(partitions, dynamic_partitions_store=instance) == all_keys
        )
        assert get_paginated_partition_keys(
            partitions, dynamic_partitions_store=instance, ascending=False
        ) == list(reversed(all_keys))
        assert instance.has_dynamic_partition("foo", "a")

        instance.delete_dynamic_partition("foo", "a")
        assert partitions.get_partition_keys(dynamic_partitions_store=instance) == ["b"]
        assert instance.has_dynamic_partition("foo", "a") is False


def test_dynamic_partitioned_run():
    with dg.instance_for_test() as instance:
        partitions_def = dg.DynamicPartitionsDefinition(name="foo")

        @dg.asset(partitions_def=partitions_def)
        def my_asset():
            return 1

        with pytest.raises(dg.DagsterUnknownPartitionError):
            dg.materialize([my_asset], instance=instance, partition_key="a")

        instance.add_dynamic_partitions("foo", ["a"])
        assert partitions_def.get_partition_keys(dynamic_partitions_store=instance) == ["a"]
        assert get_paginated_partition_keys(partitions_def, dynamic_partitions_store=instance) == [
            "a"
        ]
        assert dg.materialize([my_asset], instance=instance, partition_key="a").success
        materialization = instance.get_latest_materialization_event(dg.AssetKey("my_asset"))
        assert materialization
        assert materialization.dagster_event.partition == "a"  # pyright: ignore[reportOptionalMemberAccess]

        with pytest.raises(CheckError):
            partitions_def.get_partition_keys()


def test_dynamic_partitioned_asset_dep():
    partitions_def = dg.DynamicPartitionsDefinition(name="fruits")

    @dg.asset(partitions_def=partitions_def)
    def asset1():
        pass

    @dg.asset(partitions_def=partitions_def, deps=[asset1])
    def asset2(context):
        assert context.partition_key == "apple"
        assert context.asset_key == "apple"
        assert context.asset_keys_for_output() == ["apple"]
        assert context.asset_key_for_input() == "apple"
        assert context.asset_keys_for_input() == ["apple"]

    with dg.instance_for_test() as instance:
        instance.add_dynamic_partitions(partitions_def.name, ["apple"])  # pyright: ignore[reportArgumentType]
        dg.materialize_to_memory([asset1], instance=instance, partition_key="apple")


def test_dynamic_partitioned_asset_io_manager_context():
    partitions_def = dg.DynamicPartitionsDefinition(name="fruits")

    class MyIOManager(dg.IOManager):
        def handle_output(self, context, obj):
            assert context.partition_key == "apple"
            assert context.asset_partition_key == "apple"
            assert context.asset_partition_keys == ["apple"]

        def load_input(self, context):
            assert context.partition_key == "apple"
            assert context.asset_partition_key == "apple"
            assert context.asset_partition_keys == ["apple"]

    @dg.asset(partitions_def=partitions_def, io_manager_key="custom_io")
    def asset1():
        return 1

    @dg.asset(
        partitions_def=partitions_def,
        io_manager_key="custom_io",
    )
    def asset2(context, asset1):
        return asset1

    with dg.instance_for_test() as instance:
        instance.add_dynamic_partitions(partitions_def.name, ["apple"])  # pyright: ignore[reportArgumentType]

        dg.materialize(
            [asset1, asset2],
            instance=instance,
            partition_key="apple",
            resources={"custom_io": MyIOManager()},
        )


def test_dynamic_partitions_no_instance_provided():
    partitions_def = dg.DynamicPartitionsDefinition(name="fruits")

    with pytest.raises(CheckError, match="instance"):
        partitions_def.get_partition_keys()


def test_dynamic_partitions_mapping():
    partitions_def = dg.DynamicPartitionsDefinition(name="fruits")

    @dg.asset(partitions_def=partitions_def)
    def dynamic1(context: AssetExecutionContext):
        assert context.partition_key == "apple"
        return 1

    @dg.asset(partitions_def=partitions_def)
    def dynamic2(context: AssetExecutionContext, dynamic1):
        assert context.asset_partition_keys_for_input("dynamic1") == ["apple"]
        assert context.partition_key == "apple"
        return 1

    @dg.asset
    def unpartitioned(context, dynamic1):
        assert context.asset_partition_keys_for_input("dynamic1") == ["apple"]
        return 1

    with dg.instance_for_test() as instance:
        instance.add_dynamic_partitions(partitions_def.name, ["apple"])  # pyright: ignore[reportArgumentType]

        dg.materialize(
            [dynamic1, dynamic2, unpartitioned], instance=instance, partition_key="apple"
        )


def test_unpartitioned_downstream_of_dynamic_asset():
    partitions = [
        "apple",
        "banana",
        "cantaloupe",
    ]

    partitions_def = dg.DynamicPartitionsDefinition(name="fruits")

    @dg.asset(partitions_def=partitions_def)
    def dynamic1(context):
        return 1

    @dg.asset
    def unpartitioned(context, dynamic1):
        assert set(context.asset_partition_keys_for_input("dynamic1")) == set(partitions)
        return 1

    with dg.instance_for_test() as instance:
        instance.add_dynamic_partitions(partitions_def.name, partitions)  # pyright: ignore[reportArgumentType]

        for partition in partitions[:-1]:
            dg.materialize([dynamic1], instance=instance, partition_key=partition)

        dg.materialize([unpartitioned, dynamic1], instance=instance, partition_key=partitions[-1])


def test_has_partition_key():
    partitions_def = dg.DynamicPartitionsDefinition(name="fruits")

    with dg.instance_for_test() as instance:
        instance.add_dynamic_partitions(partitions_def.name, ["apple", "banana"])  # pyright: ignore[reportArgumentType]
        assert partitions_def.has_partition_key("apple", dynamic_partitions_store=instance)
        assert partitions_def.has_partition_key("banana", dynamic_partitions_store=instance)
        assert not partitions_def.has_partition_key("peach", dynamic_partitions_store=instance)
