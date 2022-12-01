from dagster import (
    AssetKey,
    DagsterEventType,
    DailyPartitionsDefinition,
    DynamicPartitionsDefinition,
    EventRecordsFilter,
    MultiPartitionKey,
    MultiPartitionsDefinition,
    StaticPartitionsDefinition,
    asset,
    define_asset_job,
)
from dagster._core.definitions.asset_graph import AssetGraph
from dagster._core.storage.partition_status_cache import get_and_update_asset_status_cache_values
from dagster._core.test_utils import instance_for_test
from dagster._utils import Counter, traced_counter


def test_get_cached_status_unpartitioned():
    @asset
    def asset1():
        return 1

    asset_graph = AssetGraph.from_assets([asset1])
    asset_job = define_asset_job("asset_job").resolve([asset1], [])

    asset_key = AssetKey("asset1")

    with instance_for_test() as instance:
        asset_records = list(instance.get_asset_records([asset_key]))
        assert len(asset_records) == 0

        asset_job.execute_in_process(instance=instance)

        cached_status = get_and_update_asset_status_cache_values(instance, asset_graph, asset_key)[
            asset_key
        ]

        assert cached_status
        assert (
            cached_status.latest_storage_id
            == next(
                iter(
                    instance.get_event_records(
                        EventRecordsFilter(
                            asset_key=AssetKey("asset1"),
                            event_type=DagsterEventType.ASSET_MATERIALIZATION,
                        ),
                        limit=1,
                    )
                )
            ).storage_id
        )
        assert cached_status.partitions_def_id is None
        assert cached_status.serialized_materialized_partition_subset is None


def test_get_cached_partition_status_by_asset():
    partitions_def = DailyPartitionsDefinition(start_date="2022-01-01")

    @asset(partitions_def=partitions_def)
    def asset1():
        return 1

    asset_key = AssetKey("asset1")
    asset_graph = AssetGraph.from_assets([asset1])
    asset_job = define_asset_job("asset_job").resolve([asset1], [])

    def _swap_partitions_def(new_partitions_def, asset, asset_graph, asset_job):
        asset._partitions_def = new_partitions_def  # pylint: disable=protected-access
        asset_job = define_asset_job("asset_job").resolve([asset], [])
        asset_graph = AssetGraph.from_assets([asset])
        return asset, asset_job, asset_graph

    with instance_for_test() as created_instance:
        traced_counter.set(Counter())

        asset_records = list(created_instance.get_asset_records([asset_key]))
        assert len(asset_records) == 0

        asset_job.execute_in_process(instance=created_instance, partition_key="2022-02-01")

        cached_status = get_and_update_asset_status_cache_values(
            created_instance, asset_graph, asset_key
        )[asset_key]
        assert cached_status
        assert cached_status.latest_storage_id
        assert cached_status.partitions_def_id
        assert cached_status.serialized_materialized_partition_subset
        materialized_keys = list(
            partitions_def.deserialize_subset(
                cached_status.serialized_materialized_partition_subset
            ).get_partition_keys()
        )
        assert len(materialized_keys) == 1
        assert "2022-02-01" in materialized_keys
        counts = traced_counter.get().counts()
        assert counts.get("DagsterInstance.get_materialization_count_by_partition") == 1

        asset_job.execute_in_process(instance=created_instance, partition_key="2022-02-02")

        cached_status = get_and_update_asset_status_cache_values(
            created_instance, asset_graph, asset_key
        )[asset_key]
        assert cached_status
        assert cached_status.latest_storage_id
        assert cached_status.partitions_def_id
        assert cached_status.serialized_materialized_partition_subset
        materialized_keys = list(
            partitions_def.deserialize_subset(
                cached_status.serialized_materialized_partition_subset
            ).get_partition_keys()
        )
        assert len(materialized_keys) == 2
        assert all(
            partition_key in materialized_keys for partition_key in ["2022-02-01", "2022-02-02"]
        )
        counts = traced_counter.get().counts()
        # Assert that get_materialization_count_by_partition is not called again via cache rebuild
        assert counts.get("DagsterInstance.get_materialization_count_by_partition") == 1

        static_partitions_def = StaticPartitionsDefinition(["a", "b", "c"])
        asset1, asset_job, asset_graph = _swap_partitions_def(
            static_partitions_def, asset1, asset_graph, asset_job
        )
        asset_job.execute_in_process(instance=created_instance, partition_key="a")
        cached_status = get_and_update_asset_status_cache_values(
            created_instance, asset_graph, asset_key
        )[asset_key]
        assert cached_status
        assert cached_status.serialized_materialized_partition_subset
        materialized_partition_subset = static_partitions_def.deserialize_subset(
            cached_status.serialized_materialized_partition_subset
        )
        assert "a" in materialized_partition_subset.get_partition_keys()
        assert all(
            partition not in materialized_partition_subset.get_partition_keys()
            for partition in ["b", "c"]
        )
        counts = traced_counter.get().counts()
        # Assert that get_materialization_count_by_partition is called again when partitions_def changes
        assert counts.get("DagsterInstance.get_materialization_count_by_partition") == 2


def test_multipartition_get_cached_partition_status():
    partitions_def = MultiPartitionsDefinition(
        {
            "ab": StaticPartitionsDefinition(["a", "b"]),
            "12": StaticPartitionsDefinition(["1", "2"]),
        }
    )

    @asset(partitions_def=partitions_def)
    def asset1():
        return 1

    asset_key = AssetKey("asset1")
    asset_graph = AssetGraph.from_assets([asset1])
    asset_job = define_asset_job("asset_job").resolve([asset1], [])

    with instance_for_test() as created_instance:
        traced_counter.set(Counter())

        asset_records = list(created_instance.get_asset_records([AssetKey("asset1")]))
        assert len(asset_records) == 0

        asset_job.execute_in_process(
            instance=created_instance, partition_key=MultiPartitionKey({"ab": "a", "12": "1"})
        )

        cached_status = get_and_update_asset_status_cache_values(
            created_instance, asset_graph, asset_key
        )[asset_key]
        assert cached_status
        assert cached_status.latest_storage_id
        assert cached_status.partitions_def_id
        assert cached_status.serialized_materialized_partition_subset
        materialized_keys = partitions_def.deserialize_subset(
            cached_status.serialized_materialized_partition_subset
        ).get_partition_keys()
        assert len(list(materialized_keys)) == 1
        assert MultiPartitionKey({"ab": "a", "12": "1"}) in materialized_keys

        counts = traced_counter.get().counts()
        assert counts.get("DagsterInstance.get_event_tags_for_asset") == 1

        asset_job.execute_in_process(
            instance=created_instance, partition_key=MultiPartitionKey({"ab": "a", "12": "2"})
        )

        cached_status = get_and_update_asset_status_cache_values(
            created_instance, asset_graph, asset_key
        )[asset_key]
        assert cached_status
        assert cached_status.serialized_materialized_partition_subset
        materialized_keys = partitions_def.deserialize_subset(
            cached_status.serialized_materialized_partition_subset
        ).get_partition_keys()
        assert len(list(materialized_keys)) == 2
        assert all(
            key in materialized_keys
            for key in [
                MultiPartitionKey({"ab": "a", "12": "1"}),
                MultiPartitionKey({"ab": "a", "12": "2"}),
            ]
        )
        counts = traced_counter.get().counts()
        # Assert that get_event_tags_for_asset is not called again when partitions_def remains the same
        assert counts.get("DagsterInstance.get_event_tags_for_asset") == 1


def test_cached_status_on_wipe():
    partitions_def = DailyPartitionsDefinition(start_date="2022-01-01")

    @asset(partitions_def=partitions_def)
    def asset1():
        return 1

    asset_key = AssetKey("asset1")
    asset_graph = AssetGraph.from_assets([asset1])
    asset_job = define_asset_job("asset_job").resolve([asset1], [])

    with instance_for_test() as created_instance:
        asset_records = list(created_instance.get_asset_records([AssetKey("asset1")]))
        assert len(asset_records) == 0

        asset_job.execute_in_process(instance=created_instance, partition_key="2022-02-01")

        cached_status = get_and_update_asset_status_cache_values(
            created_instance, asset_graph, asset_key
        )[asset_key]
        assert cached_status
        assert cached_status.serialized_materialized_partition_subset
        materialized_keys = list(
            partitions_def.deserialize_subset(
                cached_status.serialized_materialized_partition_subset
            ).get_partition_keys()
        )
        assert len(materialized_keys) == 1
        assert "2022-02-01" in materialized_keys


def test_dynamic_partitions_status_not_cached():
    dynamic_fn = lambda _current_time: ["a_partition"]
    dynamic = DynamicPartitionsDefinition(dynamic_fn)

    @asset(partitions_def=dynamic)
    def asset1():
        return 1

    asset_key = AssetKey("asset1")
    asset_graph = AssetGraph.from_assets([asset1])
    asset_job = define_asset_job("asset_job").resolve([asset1], [])

    with instance_for_test() as created_instance:
        asset_records = list(created_instance.get_asset_records([AssetKey("asset1")]))
        assert len(asset_records) == 0

        asset_job.execute_in_process(instance=created_instance, partition_key="a_partition")

        cached_status = get_and_update_asset_status_cache_values(
            created_instance, asset_graph, asset_key
        )[asset_key]
        assert cached_status.serialized_materialized_partition_subset is None
