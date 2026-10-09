import dagster as dg
from dagster import DagsterEventType
from dagster._core.definitions.events import AssetKeyPartitionKey
from dagster._core.loader import LoadingContextForTest
from dagster._utils.caching_instance_queryer import (
    DYNAMIC_PARTITION_LOOKUP_LIMIT,
    CachingInstanceQueryer,
)


def test_updated_after_cursor_uses_cursor_filtered_storage_query(monkeypatch):
    partitions_def = dg.StaticPartitionsDefinition(["p1", "p2", "p3"])

    @dg.asset(partitions_def=partitions_def)
    def a() -> None: ...

    asset_graph = dg.Definitions(assets=[a]).resolve_asset_graph()

    with dg.instance_for_test() as instance:
        for partition_key in ["p1", "p2"]:
            assert dg.materialize([a], instance=instance, partition_key=partition_key).success
        cursor = instance.get_latest_storage_id_by_partition(
            a.key, DagsterEventType.ASSET_MATERIALIZATION
        )["p1"]
        assert dg.materialize([a], instance=instance, partition_key="p3").success
        storage_ids = instance.get_latest_storage_id_by_partition(
            a.key, DagsterEventType.ASSET_MATERIALIZATION
        )

        calls: list[tuple[set[str] | None, int | None]] = []
        original = instance.get_latest_storage_id_by_partition

        def _spy(asset_key, event_type, partitions=None, after_cursor=None):
            calls.append((partitions, after_cursor))
            return original(asset_key, event_type, partitions, after_cursor)

        monkeypatch.setattr(instance, "get_latest_storage_id_by_partition", _spy)

        def _partition(partition_key: str) -> AssetKeyPartitionKey:
            return AssetKeyPartitionKey(a.key, partition_key)

        # with a cursor, only the filtered query is issued and only newer partitions come back
        queryer = CachingInstanceQueryer(instance, asset_graph, LoadingContextForTest(instance))
        assert queryer.get_asset_partitions_updated_after_cursor(
            a.key,
            asset_partitions=None,
            after_cursor=cursor,
            respect_materialization_data_versions=False,
        ) == {_partition("p2"), _partition("p3")}
        assert calls == [(None, cursor)]

        # single-partition lookups for updated partitions are served from that result
        assert (
            queryer.get_latest_materialization_or_observation_storage_id(_partition("p3"))
            == storage_ids["p3"]
        )
        assert len(calls) == 1

        # a partition outside the filtered result falls back to the full mapping
        assert (
            queryer.get_latest_materialization_or_observation_storage_id(_partition("p1"))
            == storage_ids["p1"]
        )
        assert calls == [(None, cursor), (None, None)]

        # without a cursor the unfiltered query is used and everything comes back
        calls.clear()
        queryer = CachingInstanceQueryer(instance, asset_graph, LoadingContextForTest(instance))
        assert queryer.get_asset_partitions_updated_after_cursor(
            a.key,
            asset_partitions=None,
            after_cursor=None,
            respect_materialization_data_versions=False,
        ) == {_partition("p1"), _partition("p2"), _partition("p3")}
        assert calls == [(None, None)]


def test_has_dynamic_partition_does_not_load_full_partition_set(monkeypatch):
    partitions_def = dg.DynamicPartitionsDefinition(name="fruits")

    @dg.asset(partitions_def=partitions_def)
    def a() -> None: ...

    asset_graph = dg.Definitions(assets=[a]).resolve_asset_graph()

    with dg.instance_for_test() as instance:
        all_keys = [f"key_{i}" for i in range(DYNAMIC_PARTITION_LOOKUP_LIMIT * 4)]
        instance.add_dynamic_partitions("fruits", all_keys)

        full_fetches: list[str] = []
        lookups: list[tuple[str, str]] = []
        original_get = instance.get_dynamic_partitions
        original_has = instance.has_dynamic_partition

        def _spy_get(partitions_def_name):
            full_fetches.append(partitions_def_name)
            return original_get(partitions_def_name)

        def _spy_has(partitions_def_name, partition_key):
            lookups.append((partitions_def_name, partition_key))
            return original_has(partitions_def_name, partition_key)

        monkeypatch.setattr(instance, "get_dynamic_partitions", _spy_get)
        monkeypatch.setattr(instance, "has_dynamic_partition", _spy_has)

        queryer = CachingInstanceQueryer(instance, asset_graph, LoadingContextForTest(instance))

        # a membership check is a single-key lookup, not a fetch of every key
        assert queryer.has_dynamic_partition("fruits", "key_0")
        assert not queryer.has_dynamic_partition("fruits", "nonexistent")
        assert full_fetches == []
        assert lookups == [("fruits", "key_0"), ("fruits", "nonexistent")]

        # repeated checks of the same key are memoized
        assert queryer.has_dynamic_partition("fruits", "key_0")
        assert len(lookups) == 2

        # a caller checking many keys loads the set once rather than issuing a lookup per key
        for key in all_keys:
            assert queryer.has_dynamic_partition("fruits", key)
        assert full_fetches == ["fruits"]
        assert len(lookups) <= DYNAMIC_PARTITION_LOOKUP_LIMIT

        # and the loaded set answers everything afterwards
        lookup_count = len(lookups)
        assert queryer.has_dynamic_partition("fruits", all_keys[-1])
        assert not queryer.has_dynamic_partition("fruits", "still_nonexistent")
        assert full_fetches == ["fruits"]
        assert len(lookups) == lookup_count

        # a queryer that already holds the full set never issues a lookup
        full_fetches.clear()
        lookups.clear()
        warm_queryer = CachingInstanceQueryer(
            instance, asset_graph, LoadingContextForTest(instance)
        )
        assert len(warm_queryer.get_dynamic_partitions("fruits")) == len(all_keys)
        assert warm_queryer.has_dynamic_partition("fruits", "key_1")
        assert not warm_queryer.has_dynamic_partition("fruits", "nonexistent")
        assert full_fetches == ["fruits"]
        assert lookups == []
