import dagster as dg
from dagster import DagsterEventType
from dagster._core.definitions.events import AssetKeyPartitionKey
from dagster._core.loader import LoadingContextForTest
from dagster._utils.caching_instance_queryer import CachingInstanceQueryer


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
        all_keys = [f"key_{i}" for i in range(200)]
        instance.add_dynamic_partitions("fruits", all_keys)

        full_fetches: list[str] = []
        membership_lookups: list[list[str]] = []
        single_key_checks: list[str] = []
        original_get = instance.get_dynamic_partitions
        original_existing = instance.get_existing_dynamic_partitions
        original_has = instance.has_dynamic_partition

        def _spy_get(partitions_def_name):
            full_fetches.append(partitions_def_name)
            return original_get(partitions_def_name)

        def _spy_existing(partitions_def_name, partition_keys):
            membership_lookups.append(sorted(partition_keys))
            return original_existing(partitions_def_name, partition_keys)

        def _spy_has(partitions_def_name, partition_key):
            single_key_checks.append(partition_key)
            return original_has(partitions_def_name, partition_key)

        monkeypatch.setattr(instance, "get_dynamic_partitions", _spy_get)
        monkeypatch.setattr(instance, "get_existing_dynamic_partitions", _spy_existing)
        monkeypatch.setattr(instance, "has_dynamic_partition", _spy_has)

        queryer = CachingInstanceQueryer(instance, asset_graph, LoadingContextForTest(instance))

        # a single-key check is the indexed single-key query, not a fetch of every key, and not
        # the batched form -- a storage with no bounded batch query answers that by loading the
        # whole definition
        assert queryer.has_dynamic_partition("fruits", "key_0")
        assert not queryer.has_dynamic_partition("fruits", "nonexistent")
        assert full_fetches == []
        assert membership_lookups == []
        assert single_key_checks == ["key_0", "nonexistent"]

        # repeated checks of a key already looked up are memoized
        assert queryer.has_dynamic_partition("fruits", "key_0")
        assert not queryer.has_dynamic_partition("fruits", "nonexistent")
        assert len(single_key_checks) == 2

        # checking every key one at a time still never loads the whole set
        for key in all_keys:
            assert queryer.has_dynamic_partition("fruits", key)
        assert full_fetches == []
        assert membership_lookups == []
        assert len(single_key_checks) == 1 + len(all_keys)

        # a bulk validation costs one query for whatever is not already known
        membership_lookups.clear()
        assert queryer.get_existing_dynamic_partitions("fruits", [*all_keys, "other"]) == set(
            all_keys
        )
        assert membership_lookups == [["other"]]

        # a queryer that already holds the full set answers from it without any lookup
        full_fetches.clear()
        membership_lookups.clear()
        warm_queryer = CachingInstanceQueryer(
            instance, asset_graph, LoadingContextForTest(instance)
        )
        assert len(warm_queryer.get_dynamic_partitions("fruits")) == len(all_keys)
        single_key_checks.clear()
        assert warm_queryer.has_dynamic_partition("fruits", "key_1")
        assert not warm_queryer.has_dynamic_partition("fruits", "nonexistent")
        assert full_fetches == ["fruits"]
        assert membership_lookups == []
        assert single_key_checks == []


def test_queryer_membership_on_a_storage_without_a_bounded_query(monkeypatch):
    """A storage that answers the batched form by loading the whole definition must not be asked
    to do so once per key, and a single-key check must stay on the indexed single-key query.
    """
    partitions_def = dg.DynamicPartitionsDefinition(name="fruits")

    @dg.asset(partitions_def=partitions_def)
    def a() -> None: ...

    asset_graph = dg.Definitions(assets=[a]).resolve_asset_graph()

    with dg.instance_for_test() as instance:
        all_keys = [f"key_{i}" for i in range(50)]
        instance.add_dynamic_partitions("fruits", all_keys)

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

        queryer = CachingInstanceQueryer(instance, asset_graph, LoadingContextForTest(instance))

        # single-key checks use the indexed query, never a full fetch
        assert queryer.has_dynamic_partition("fruits", "key_0")
        assert not queryer.has_dynamic_partition("fruits", "nope")
        assert queryer.has_dynamic_partition("fruits", "key_1")
        assert full_fetches == []
        assert single_key_checks == ["key_0", "nope", "key_1"]

        # a batched check falls back to one full fetch, reused for every later batch
        assert queryer.get_existing_dynamic_partitions("fruits", ["key_2", "key_3", "nope"]) == {
            "key_2",
            "key_3",
        }
        assert queryer.get_existing_dynamic_partitions("fruits", ["key_4"]) == {"key_4"}
        assert full_fetches == ["fruits"]
        assert len(single_key_checks) == 3
