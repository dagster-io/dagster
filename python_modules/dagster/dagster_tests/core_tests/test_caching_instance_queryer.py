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
