from collections.abc import Callable, Sequence
from datetime import datetime

import dagster as dg
import pytest
from dagster import AssetExecutionContext
from dagster._check import CheckError
from dagster._core.definitions.partitions.context import partition_loading_context
from dagster._core.test_utils import get_paginated_partition_keys


@pytest.mark.parametrize(
    argnames=["partition_fn"],
    argvalues=[
        (lambda _current_time: [dg.Partition("a_partition")],),
        (lambda _current_time: [dg.Partition(x) for x in range(10)],),
    ],
)
def test_dynamic_partitions_partitions(
    partition_fn: Callable[[datetime | None], Sequence[dg.Partition]],
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
def test_dynamic_partitions_keys(partition_fn: Callable[[datetime | None], Sequence[str]]):
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


def test_get_existing_dynamic_partitions():
    from dagster._core.instance.types import DynamicPartitionsStoreAfterRequests
    from dagster._core.storage.event_log.sql_event_log import (
        DYNAMIC_PARTITION_MEMBERSHIP_CHUNK_SIZE,
    )

    partitions = dg.DynamicPartitionsDefinition(name="foo")
    # more keys than fit in one `partition IN (...)` query, so the chunking is exercised
    all_keys = [f"key_{i}" for i in range(DYNAMIC_PARTITION_MEMBERSHIP_CHUNK_SIZE + 200)]

    with dg.instance_for_test() as instance:
        instance.add_dynamic_partitions("foo", all_keys)

        assert instance.get_existing_dynamic_partitions("foo", []) == set()
        assert instance.get_existing_dynamic_partitions("foo", ["key_0", "nope"]) == {"key_0"}
        assert instance.get_existing_dynamic_partitions("foo", [*all_keys, "nope"]) == set(all_keys)
        assert instance.get_existing_dynamic_partitions("other_def", ["key_0"]) == set()

        with partition_loading_context(dynamic_partitions_store=instance):
            assert partitions.filter_valid_partition_keys({"key_0", "key_1", "nope"}) == {
                "key_0",
                "key_1",
            }

        # the after-requests view layers pending adds and deletes over the stored keys
        store = DynamicPartitionsStoreAfterRequests.from_requests(
            instance,
            [
                partitions.build_add_request(["pending"]),
                partitions.build_delete_request(["key_0"]),
            ],
        )
        assert store.get_existing_dynamic_partitions(
            "foo", ["key_0", "key_1", "pending", "nope"]
        ) == {"key_1", "pending"}
        assert store.has_dynamic_partition("foo", "pending")
        assert not store.has_dynamic_partition("foo", "key_0")


def test_membership_checks_on_a_storage_without_a_bounded_query(monkeypatch):
    """A storage that answers the batched form by loading the whole definition must not be asked
    to do so once per key, and a single-key check must stay on the indexed single-key query.
    """
    from dagster._core.instance.types import CachingDynamicPartitionsLoader

    all_keys = [f"key_{i}" for i in range(50)]

    with dg.instance_for_test() as instance:
        instance.add_dynamic_partitions("foo", all_keys)

        full_fetches: list[str] = []
        single_key_checks: list[str] = []
        original_get = instance.get_dynamic_partitions
        original_has = instance.has_dynamic_partition

        def _spy_get(partitions_def_name):
            full_fetches.append(partitions_def_name)
            return original_get(partitions_def_name)

        def _spy_has(partitions_def_name, partition_key):
            single_key_checks.append(partition_key)
            return original_has(partitions_def_name, partition_key)

        monkeypatch.setattr(instance, "get_dynamic_partitions", _spy_get)
        monkeypatch.setattr(instance, "has_dynamic_partition", _spy_has)
        monkeypatch.setattr(
            type(instance.event_log_storage),
            "has_bounded_dynamic_partition_membership_query",
            property(lambda _self: False),
        )

        loader = CachingDynamicPartitionsLoader(instance)

        # single-key checks use the indexed query, never a full fetch
        assert loader.has_dynamic_partition("foo", "key_0")
        assert not loader.has_dynamic_partition("foo", "nope")
        assert loader.has_dynamic_partition("foo", "key_1")
        assert full_fetches == []
        assert single_key_checks == ["key_0", "nope", "key_1"]

        # a batched check falls back to one full fetch, reused for every later batch
        assert loader.get_existing_dynamic_partitions("foo", ["key_2", "key_3", "nope"]) == {
            "key_2",
            "key_3",
        }
        assert loader.get_existing_dynamic_partitions("foo", ["key_4", "key_5"]) == {
            "key_4",
            "key_5",
        }
        assert full_fetches == ["foo"]
        assert len(single_key_checks) == 3


def test_filter_valid_multipartition_keys_stays_bounded(monkeypatch):
    dynamic_dim = dg.DynamicPartitionsDefinition(name="foo")
    partitions_def = dg.MultiPartitionsDefinition(
        {"dyn": dynamic_dim, "static": dg.StaticPartitionsDefinition(["s1", "s2"])}
    )

    with dg.instance_for_test() as instance:
        instance.add_dynamic_partitions("foo", [f"key_{i}" for i in range(50)])

        full_fetches: list[str] = []
        original_get = instance.get_dynamic_partitions

        def _spy_get(partitions_def_name):
            full_fetches.append(partitions_def_name)
            return original_get(partitions_def_name)

        monkeypatch.setattr(instance, "get_dynamic_partitions", _spy_get)

        with partition_loading_context(dynamic_partitions_store=instance):
            # nothing to validate must not touch storage at all
            assert partitions_def.filter_valid_partition_keys(set()) == set()
            assert full_fetches == []

            # and a handful of candidates validates only the keys they reference
            valid = partitions_def.filter_valid_partition_keys(
                {"key_1|s1", "key_2|s2", "nope|s1", "key_3|not_a_static_key", "malformed"}
            )
            assert {str(key) for key in valid} == {"key_1|s1", "key_2|s2"}
            assert full_fetches == []


def test_dynamic_partitions_pagination_does_not_load_full_partition_set(monkeypatch):
    partitions = dg.DynamicPartitionsDefinition(name="foo")
    all_keys = [f"key_{i}" for i in range(20)]

    with dg.instance_for_test() as instance:
        instance.add_dynamic_partitions("foo", all_keys)

        full_fetches: list[str] = []
        original_get = instance.get_dynamic_partitions

        def _spy_get(partitions_def_name):
            full_fetches.append(partitions_def_name)
            return original_get(partitions_def_name)

        monkeypatch.setattr(instance, "get_dynamic_partitions", _spy_get)

        # each page is fetched from storage rather than sliced out of the whole key set
        assert (
            get_paginated_partition_keys(
                partitions, dynamic_partitions_store=instance, batch_size=5
            )
            == all_keys
        )
        assert get_paginated_partition_keys(
            partitions, dynamic_partitions_store=instance, batch_size=5, ascending=False
        ) == list(reversed(all_keys))
        assert full_fetches == []


def test_dynamic_partitions_pagination_cursor_and_has_more():
    from dagster._core.definitions.partitions.context import (
        PartitionLoadingContext,
        TemporalContext,
    )
    from dagster._core.types.pagination import ValueIndexCursor

    partitions = dg.DynamicPartitionsDefinition(name="foo")
    all_keys = [f"key_{i}" for i in range(4)]

    with dg.instance_for_test() as instance:
        instance.add_dynamic_partitions("foo", all_keys)
        context = PartitionLoadingContext(
            temporal_context=TemporalContext(effective_dt=datetime.now(), last_event_id=None),
            dynamic_partitions_store=instance,
        )

        # a page that exactly consumes the remaining keys reports no more, rather than handing
        # back a cursor that yields an empty page
        page = partitions.get_paginated_partition_keys(context=context, limit=2, ascending=True)
        assert page.results == all_keys[:2]
        assert page.has_more

        page = partitions.get_paginated_partition_keys(
            context=context, limit=2, ascending=True, cursor=page.cursor
        )
        assert page.results == all_keys[2:]
        assert not page.has_more

        # a cursor this store cannot read restarts from the first page instead of raising
        foreign_cursor = ValueIndexCursor(value="key_1").to_string()
        page = partitions.get_paginated_partition_keys(
            context=context, limit=2, ascending=True, cursor=foreign_cursor
        )
        assert page.results == all_keys[:2]


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
        assert materialization.dagster_event.partition == "a"  # ty: ignore[unresolved-attribute]

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
        instance.add_dynamic_partitions(partitions_def.name, ["apple"])  # ty: ignore[invalid-argument-type]
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
        instance.add_dynamic_partitions(partitions_def.name, ["apple"])  # ty: ignore[invalid-argument-type]

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
        instance.add_dynamic_partitions(partitions_def.name, ["apple"])  # ty: ignore[invalid-argument-type]

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
        instance.add_dynamic_partitions(partitions_def.name, partitions)  # ty: ignore[invalid-argument-type]

        for partition in partitions[:-1]:
            dg.materialize([dynamic1], instance=instance, partition_key=partition)

        dg.materialize([unpartitioned, dynamic1], instance=instance, partition_key=partitions[-1])


def test_has_partition_key():
    partitions_def = dg.DynamicPartitionsDefinition(name="fruits")

    with dg.instance_for_test() as instance:
        instance.add_dynamic_partitions(partitions_def.name, ["apple", "banana"])  # ty: ignore[invalid-argument-type]
        assert partitions_def.has_partition_key("apple", dynamic_partitions_store=instance)
        assert partitions_def.has_partition_key("banana", dynamic_partitions_store=instance)
        assert not partitions_def.has_partition_key("peach", dynamic_partitions_store=instance)
