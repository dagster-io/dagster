import time

from dagster import (
    AssetKey,
    AssetMaterialization,
    DagsterEventType,
    DailyPartitionsDefinition,
    DynamicPartitionsDefinition,
    EventLogEntry,
    EventRecordsFilter,
    MultiPartitionKey,
    MultiPartitionsDefinition,
    StaticPartitionsDefinition,
    asset,
    define_asset_job,
)
from dagster._core.definitions.internal_asset_graph import InternalAssetGraph
from dagster._core.definitions.time_window_partitions import HourlyPartitionsDefinition
from dagster._core.events import (
    AssetMaterializationPlannedData,
    DagsterEvent,
    StepMaterializationData,
)
from dagster._core.storage.dagster_run import DagsterRunStatus
from dagster._core.storage.partition_status_cache import (
    RUN_FETCH_BATCH_SIZE,
    AssetStatusCacheValue,
    build_failed_and_in_progress_partition_subset,
    get_and_update_asset_status_cache_value,
)
from dagster._core.test_utils import create_run_for_test, instance_for_test
from dagster._core.utils import make_new_run_id
from dagster._utils import Counter, traced_counter

from .utils.event_log_storage import (
    create_and_delete_test_runs,
)


def test_get_cached_status_unpartitioned():
    @asset
    def asset1():
        return 1

    asset_graph = InternalAssetGraph.from_assets([asset1])
    asset_job = define_asset_job("asset_job").resolve(asset_graph=asset_graph)

    asset_key = AssetKey("asset1")

    with instance_for_test() as instance:
        asset_records = list(instance.get_asset_records([asset_key]))
        assert len(asset_records) == 0

        asset_job.execute_in_process(instance=instance)

        cached_status = get_and_update_asset_status_cache_value(
            instance, asset_key, asset_graph.get_partitions_def(asset_key)
        )

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
        assert cached_status.serialized_failed_partition_subset is None


def test_get_cached_partition_status_changed_time_partitions():
    original_partitions_def = HourlyPartitionsDefinition(start_date="2022-01-01-00:00")
    new_partitions_def = DailyPartitionsDefinition(start_date="2022-01-01")

    @asset(partitions_def=original_partitions_def)
    def asset1():
        return 1

    asset_key = AssetKey("asset1")
    asset_graph = InternalAssetGraph.from_assets([asset1])
    asset_job = define_asset_job("asset_job").resolve(asset_graph=asset_graph)

    def _swap_partitions_def(new_partitions_def, asset, asset_graph, asset_job):
        asset._partitions_def = new_partitions_def  # noqa: SLF001
        asset_graph = InternalAssetGraph.from_assets([asset])
        asset_job = define_asset_job("asset_job").resolve(asset_graph=asset_graph)
        return asset, asset_job, asset_graph

    with instance_for_test() as created_instance:
        traced_counter.set(Counter())

        asset_records = list(created_instance.get_asset_records([asset_key]))
        assert len(asset_records) == 0

        asset_job.execute_in_process(instance=created_instance, partition_key="2022-02-01-00:00")

        # swap the partitions def and kick off a run before we try to get the cached status
        asset1, asset_job, asset_graph = _swap_partitions_def(
            new_partitions_def, asset1, asset_graph, asset_job
        )
        asset_job.execute_in_process(instance=created_instance, partition_key="2022-02-02")

        cached_status = get_and_update_asset_status_cache_value(
            created_instance, asset_key, asset_graph.get_partitions_def(asset_key)
        )

        assert cached_status
        assert cached_status.latest_storage_id
        assert cached_status.partitions_def_id
        assert cached_status.serialized_materialized_partition_subset
        materialized_keys = list(
            new_partitions_def.deserialize_subset(
                cached_status.serialized_materialized_partition_subset
            ).get_partition_keys()
        )
        assert set(materialized_keys) == {"2022-02-02"}
        counts = traced_counter.get().counts()
        assert counts.get("DagsterInstance.get_materialized_partitions") == 1


def test_get_cached_partition_status_by_asset():
    partitions_def = DailyPartitionsDefinition(start_date="2022-01-01")

    @asset(partitions_def=partitions_def)
    def asset1():
        return 1

    asset_key = AssetKey("asset1")
    asset_graph = InternalAssetGraph.from_assets([asset1])
    asset_job = define_asset_job("asset_job").resolve(asset_graph=asset_graph)

    def _swap_partitions_def(new_partitions_def, asset, asset_graph, asset_job):
        asset._partitions_def = new_partitions_def  # noqa: SLF001
        asset_graph = InternalAssetGraph.from_assets([asset])
        asset_job = define_asset_job("asset_job").resolve(asset_graph=asset_graph)
        return asset, asset_job, asset_graph

    with instance_for_test() as created_instance:
        traced_counter.set(Counter())

        asset_records = list(created_instance.get_asset_records([asset_key]))
        assert len(asset_records) == 0

        asset_job.execute_in_process(instance=created_instance, partition_key="2022-02-01")

        cached_status = get_and_update_asset_status_cache_value(
            created_instance, asset_key, asset_graph.get_partitions_def(asset_key)
        )
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
        assert counts.get("DagsterInstance.get_materialized_partitions") == 1

        asset_job.execute_in_process(instance=created_instance, partition_key="2022-02-02")

        cached_status = get_and_update_asset_status_cache_value(
            created_instance, asset_key, asset_graph.get_partitions_def(asset_key)
        )
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

        static_partitions_def = StaticPartitionsDefinition(["a", "b", "c"])
        asset1, asset_job, asset_graph = _swap_partitions_def(
            static_partitions_def, asset1, asset_graph, asset_job
        )
        asset_job.execute_in_process(instance=created_instance, partition_key="a")
        cached_status = get_and_update_asset_status_cache_value(
            created_instance, asset_key, asset_graph.get_partitions_def(asset_key)
        )
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
    asset_graph = InternalAssetGraph.from_assets([asset1])
    asset_job = define_asset_job("asset_job").resolve(asset_graph=asset_graph)

    with instance_for_test() as created_instance:
        traced_counter.set(Counter())

        asset_records = list(created_instance.get_asset_records([AssetKey("asset1")]))
        assert len(asset_records) == 0

        asset_job.execute_in_process(
            instance=created_instance, partition_key=MultiPartitionKey({"ab": "a", "12": "1"})
        )

        cached_status = get_and_update_asset_status_cache_value(
            created_instance, asset_key, asset_graph.get_partitions_def(asset_key)
        )
        assert cached_status
        assert cached_status.latest_storage_id
        assert cached_status.partitions_def_id
        assert cached_status.serialized_materialized_partition_subset
        materialized_keys = partitions_def.deserialize_subset(
            cached_status.serialized_materialized_partition_subset
        ).get_partition_keys()
        assert len(list(materialized_keys)) == 1
        assert MultiPartitionKey({"ab": "a", "12": "1"}) in materialized_keys

        asset_job.execute_in_process(
            instance=created_instance, partition_key=MultiPartitionKey({"ab": "a", "12": "2"})
        )

        cached_status = get_and_update_asset_status_cache_value(
            created_instance, asset_key, asset_graph.get_partitions_def(asset_key)
        )
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


def test_cached_status_on_wipe():
    partitions_def = DailyPartitionsDefinition(start_date="2022-01-01")

    @asset(partitions_def=partitions_def)
    def asset1():
        return 1

    asset_key = AssetKey("asset1")
    asset_graph = InternalAssetGraph.from_assets([asset1])
    asset_job = define_asset_job("asset_job").resolve(asset_graph=asset_graph)

    with instance_for_test() as created_instance:
        asset_records = list(created_instance.get_asset_records([AssetKey("asset1")]))
        assert len(asset_records) == 0

        asset_job.execute_in_process(instance=created_instance, partition_key="2022-02-01")

        cached_status = get_and_update_asset_status_cache_value(
            created_instance, asset_key, asset_graph.get_partitions_def(asset_key)
        )
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
    asset_graph = InternalAssetGraph.from_assets([asset1])
    asset_job = define_asset_job("asset_job").resolve(asset_graph=asset_graph)

    with instance_for_test() as created_instance:
        asset_records = list(created_instance.get_asset_records([AssetKey("asset1")]))
        assert len(asset_records) == 0

        asset_job.execute_in_process(instance=created_instance, partition_key="a_partition")

        cached_status = get_and_update_asset_status_cache_value(
            created_instance, asset_key, asset_graph.get_partitions_def(asset_key)
        )
        assert cached_status
        assert cached_status.serialized_materialized_partition_subset is None


def test_failure_cache():
    partitions_def = StaticPartitionsDefinition(["good1", "good2", "fail1", "fail2"])

    @asset(partitions_def=partitions_def)
    def asset1(context):
        if context.partition_key.startswith("fail"):
            raise Exception()

    asset_key = AssetKey("asset1")
    asset_graph = InternalAssetGraph.from_assets([asset1])
    asset_job = define_asset_job("asset_job").resolve(asset_graph=asset_graph)

    with instance_for_test() as created_instance:
        # no events
        cached_status = get_and_update_asset_status_cache_value(
            created_instance, asset_key, asset_graph.get_partitions_def(asset_key)
        )
        assert not cached_status

        asset_job.execute_in_process(
            instance=created_instance, partition_key="fail1", raise_on_error=False
        )

        cached_status = get_and_update_asset_status_cache_value(
            created_instance, asset_key, asset_graph.get_partitions_def(asset_key)
        )
        # failed partition
        assert partitions_def.deserialize_subset(
            cached_status.serialized_failed_partition_subset
        ).get_partition_keys() == {"fail1"}
        assert (
            cached_status.deserialize_in_progress_partition_subsets(
                partitions_def
            ).get_partition_keys()
            == set()
        )

        asset_job.execute_in_process(
            instance=created_instance, partition_key="good1", raise_on_error=False
        )
        asset_job.execute_in_process(
            instance=created_instance, partition_key="fail2", raise_on_error=False
        )

        cached_status = get_and_update_asset_status_cache_value(
            created_instance, asset_key, asset_graph.get_partitions_def(asset_key)
        )
        # cache is updated with new failed partition, successful partition is ignored
        assert partitions_def.deserialize_subset(
            cached_status.serialized_failed_partition_subset
        ).get_partition_keys() == {"fail1", "fail2"}
        assert (
            cached_status.deserialize_in_progress_partition_subsets(
                partitions_def
            ).get_partition_keys()
            == set()
        )

        run_1 = create_run_for_test(created_instance)
        created_instance.event_log_storage.store_event(
            EventLogEntry(
                error_info=None,
                level="debug",
                user_message="",
                run_id=run_1.run_id,
                timestamp=time.time(),
                dagster_event=DagsterEvent(
                    DagsterEventType.ASSET_MATERIALIZATION.value,
                    "nonce",
                    event_specific_data=StepMaterializationData(
                        AssetMaterialization(asset_key=asset_key, partition="fail1")
                    ),
                ),
            )
        )

        cached_status = get_and_update_asset_status_cache_value(
            created_instance, asset_key, asset_graph.get_partitions_def(asset_key)
        )
        # cache is updated after successful materialization of fail1
        assert partitions_def.deserialize_subset(
            cached_status.serialized_failed_partition_subset
        ).get_partition_keys() == {"fail2"}
        assert (
            cached_status.deserialize_in_progress_partition_subsets(
                partitions_def
            ).get_partition_keys()
            == set()
        )

        run_2 = create_run_for_test(created_instance)
        created_instance.event_log_storage.store_event(
            EventLogEntry(
                error_info=None,
                level="debug",
                user_message="",
                run_id=run_2.run_id,
                timestamp=time.time(),
                dagster_event=DagsterEvent(
                    DagsterEventType.ASSET_MATERIALIZATION_PLANNED.value,
                    "nonce",
                    event_specific_data=AssetMaterializationPlannedData(asset_key, "good2"),
                ),
            )
        )

        cached_status = get_and_update_asset_status_cache_value(
            created_instance, asset_key, asset_graph.get_partitions_def(asset_key)
        )
        # in progress materialization is ignored
        assert partitions_def.deserialize_subset(
            cached_status.serialized_failed_partition_subset
        ).get_partition_keys() == {"fail2"}
        assert cached_status.deserialize_in_progress_partition_subsets(
            partitions_def
        ).get_partition_keys() == {"good2"}


def test_failure_cache_added():
    partitions_def = StaticPartitionsDefinition(["good1", "good2", "fail1", "fail2"])

    @asset(partitions_def=partitions_def)
    def asset1(context):
        if context.partition_key.startswith("fail"):
            raise Exception()

    asset_key = AssetKey("asset1")
    asset_graph = InternalAssetGraph.from_assets([asset1])
    asset_job = define_asset_job("asset_job").resolve(asset_graph=asset_graph)

    with instance_for_test() as created_instance:
        created_instance.update_asset_cached_status_data(
            asset_key,
            AssetStatusCacheValue(
                latest_storage_id=0,
                partitions_def_id=partitions_def.get_serializable_unique_identifier(),
            ),
        )

        asset_job.execute_in_process(
            instance=created_instance, partition_key="fail1", raise_on_error=False
        )

        cached_status = get_and_update_asset_status_cache_value(
            created_instance, asset_key, asset_graph.get_partitions_def(asset_key)
        )
        # failed partition
        assert partitions_def.deserialize_subset(
            cached_status.serialized_failed_partition_subset
        ).get_partition_keys() == {"fail1"}


def test_failure_cache_in_progress_runs():
    partitions_def = StaticPartitionsDefinition(["good1", "good2", "fail1", "fail2"])

    @asset(partitions_def=partitions_def)
    def asset1(context):
        if context.partition_key.startswith("fail"):
            raise Exception()

    asset_key = AssetKey("asset1")
    asset_graph = InternalAssetGraph.from_assets([asset1])
    define_asset_job("asset_job").resolve(asset_graph=asset_graph)

    with instance_for_test() as created_instance:
        run_1 = create_run_for_test(created_instance)
        created_instance.event_log_storage.store_event(
            EventLogEntry(
                error_info=None,
                level="debug",
                user_message="",
                run_id=run_1.run_id,
                timestamp=time.time(),
                dagster_event=DagsterEvent(
                    DagsterEventType.ASSET_MATERIALIZATION_PLANNED.value,
                    "nonce",
                    event_specific_data=AssetMaterializationPlannedData(
                        asset_key=asset_key, partition="fail1"
                    ),
                ),
            )
        )

        cached_status = get_and_update_asset_status_cache_value(
            created_instance, asset_key, asset_graph.get_partitions_def(asset_key)
        )

        created_instance.report_run_failed(run_1)

        cached_status = get_and_update_asset_status_cache_value(
            created_instance, asset_key, asset_graph.get_partitions_def(asset_key)
        )
        assert cached_status.deserialize_failed_partition_subsets(
            partitions_def
        ).get_partition_keys() == {"fail1"}
        assert (
            cached_status.deserialize_in_progress_partition_subsets(
                partitions_def
            ).get_partition_keys()
            == set()
        )

        run_2 = create_run_for_test(created_instance, status=DagsterRunStatus.STARTED)
        created_instance.event_log_storage.store_event(
            EventLogEntry(
                error_info=None,
                level="debug",
                user_message="",
                run_id=run_2.run_id,
                timestamp=time.time(),
                dagster_event=DagsterEvent(
                    DagsterEventType.ASSET_MATERIALIZATION_PLANNED.value,
                    "nonce",
                    event_specific_data=AssetMaterializationPlannedData(
                        asset_key=asset_key, partition="fail2"
                    ),
                ),
            )
        )

        cached_status = get_and_update_asset_status_cache_value(
            created_instance, asset_key, asset_graph.get_partitions_def(asset_key)
        )
        assert cached_status.deserialize_failed_partition_subsets(
            partitions_def
        ).get_partition_keys() == {"fail1"}
        assert cached_status.deserialize_in_progress_partition_subsets(
            partitions_def
        ).get_partition_keys() == {"fail2"}

        created_instance.report_run_failed(run_2)

        cached_status = get_and_update_asset_status_cache_value(
            created_instance, asset_key, asset_graph.get_partitions_def(asset_key)
        )
        assert cached_status.deserialize_failed_partition_subsets(
            partitions_def
        ).get_partition_keys() == {"fail1", "fail2"}
        assert (
            cached_status.deserialize_in_progress_partition_subsets(
                partitions_def
            ).get_partition_keys()
            == set()
        )


def test_cache_cancelled_runs():
    partitions_def = StaticPartitionsDefinition(["good1", "good2", "fail1", "fail2"])

    @asset(partitions_def=partitions_def)
    def asset1(context):
        if context.partition_key.startswith("fail"):
            raise Exception()

    asset_key = AssetKey("asset1")
    asset_graph = InternalAssetGraph.from_assets([asset1])
    define_asset_job("asset_job").resolve(asset_graph=asset_graph)

    with instance_for_test() as created_instance:
        run_1 = create_run_for_test(created_instance)
        created_instance.event_log_storage.store_event(
            EventLogEntry(
                error_info=None,
                level="debug",
                user_message="",
                run_id=run_1.run_id,
                timestamp=time.time(),
                dagster_event=DagsterEvent(
                    DagsterEventType.ASSET_MATERIALIZATION_PLANNED.value,
                    "nonce",
                    event_specific_data=AssetMaterializationPlannedData(
                        asset_key=asset_key, partition="fail1"
                    ),
                ),
            )
        )

        cached_status = get_and_update_asset_status_cache_value(
            created_instance, asset_key, asset_graph.get_partitions_def(asset_key)
        )
        early_id = cached_status.earliest_in_progress_materialization_event_id
        assert cached_status.deserialize_in_progress_partition_subsets(
            partitions_def
        ).get_partition_keys() == {"fail1"}

        run_2 = create_run_for_test(created_instance, status=DagsterRunStatus.STARTED)
        created_instance.event_log_storage.store_event(
            EventLogEntry(
                error_info=None,
                level="debug",
                user_message="",
                run_id=run_2.run_id,
                timestamp=time.time(),
                dagster_event=DagsterEvent(
                    DagsterEventType.ASSET_MATERIALIZATION_PLANNED.value,
                    "nonce",
                    event_specific_data=AssetMaterializationPlannedData(
                        asset_key=asset_key, partition="fail2"
                    ),
                ),
            )
        )

        cached_status = get_and_update_asset_status_cache_value(
            created_instance, asset_key, asset_graph.get_partitions_def(asset_key)
        )
        assert (
            partitions_def.deserialize_subset(
                cached_status.serialized_failed_partition_subset
            ).get_partition_keys()
            == set()
        )
        assert cached_status.deserialize_in_progress_partition_subsets(
            partitions_def
        ).get_partition_keys() == {"fail1", "fail2"}
        assert cached_status.earliest_in_progress_materialization_event_id == early_id

        created_instance.report_run_failed(run_2)

        cached_status = get_and_update_asset_status_cache_value(
            created_instance, asset_key, asset_graph.get_partitions_def(asset_key)
        )
        assert partitions_def.deserialize_subset(
            cached_status.serialized_failed_partition_subset
        ).get_partition_keys() == {"fail2"}
        assert cached_status.deserialize_in_progress_partition_subsets(
            partitions_def
        ).get_partition_keys() == {"fail1"}
        assert cached_status.earliest_in_progress_materialization_event_id == early_id

        created_instance.report_run_canceled(run_1)

        cached_status = get_and_update_asset_status_cache_value(
            created_instance, asset_key, asset_graph.get_partitions_def(asset_key)
        )
        assert partitions_def.deserialize_subset(
            cached_status.serialized_failed_partition_subset
        ).get_partition_keys() == {"fail2"}
        assert (
            cached_status.deserialize_in_progress_partition_subsets(
                partitions_def
            ).get_partition_keys()
            == set()
        )
        assert cached_status.earliest_in_progress_materialization_event_id is None


def test_failure_cache_concurrent_materializations():
    partitions_def = StaticPartitionsDefinition(["good1", "good2", "fail1", "fail2"])

    @asset(partitions_def=partitions_def)
    def asset1(context):
        if context.partition_key.startswith("fail"):
            raise Exception()

    asset_key = AssetKey("asset1")
    asset_graph = InternalAssetGraph.from_assets([asset1])
    define_asset_job("asset_job").resolve(asset_graph=asset_graph)

    with instance_for_test() as created_instance:
        run_1 = create_run_for_test(created_instance)
        created_instance.event_log_storage.store_event(
            EventLogEntry(
                error_info=None,
                level="debug",
                user_message="",
                run_id=run_1.run_id,
                timestamp=time.time(),
                dagster_event=DagsterEvent(
                    DagsterEventType.ASSET_MATERIALIZATION_PLANNED.value,
                    "nonce",
                    event_specific_data=AssetMaterializationPlannedData(
                        asset_key=asset_key, partition="fail1"
                    ),
                ),
            )
        )

        run_2 = create_run_for_test(created_instance)
        created_instance.event_log_storage.store_event(
            EventLogEntry(
                error_info=None,
                level="debug",
                user_message="",
                run_id=run_2.run_id,
                timestamp=time.time(),
                dagster_event=DagsterEvent(
                    DagsterEventType.ASSET_MATERIALIZATION_PLANNED.value,
                    "nonce",
                    event_specific_data=AssetMaterializationPlannedData(
                        asset_key=asset_key, partition="fail1"
                    ),
                ),
            )
        )

        cached_status = get_and_update_asset_status_cache_value(
            created_instance, asset_key, asset_graph.get_partitions_def(asset_key)
        )
        assert cached_status.deserialize_in_progress_partition_subsets(
            partitions_def
        ).get_partition_keys() == {"fail1"}
        assert cached_status.earliest_in_progress_materialization_event_id is not None

        created_instance.report_run_failed(run_2)

        cached_status = get_and_update_asset_status_cache_value(
            created_instance, asset_key, asset_graph.get_partitions_def(asset_key)
        )
        assert partitions_def.deserialize_subset(
            cached_status.serialized_failed_partition_subset
        ).get_partition_keys() == {"fail1"}
        assert (
            cached_status.deserialize_in_progress_partition_subsets(
                partitions_def
            ).get_partition_keys()
            == set()
        )
        # run_1 is still in progress, but run_2 started after and failed, so we move on
        assert cached_status.earliest_in_progress_materialization_event_id is None


def test_failed_partitioned_asset_converted_to_multipartitioned():
    daily_def = DailyPartitionsDefinition("2023-01-01")

    @asset(
        partitions_def=daily_def,
    )
    def my_asset():
        raise Exception("oops")

    with instance_for_test() as created_instance:
        asset_graph = InternalAssetGraph.from_assets([my_asset])
        my_job = define_asset_job("asset_job", partitions_def=daily_def).resolve(
            asset_graph=asset_graph
        )

        my_job.execute_in_process(
            instance=created_instance, partition_key="2023-01-01", raise_on_error=False
        )

        my_asset._partitions_def = MultiPartitionsDefinition(  # noqa: SLF001
            partitions_defs={
                "a": DailyPartitionsDefinition("2023-01-01"),
                "b": StaticPartitionsDefinition(["a", "b"]),
            }
        )
        asset_graph = InternalAssetGraph.from_assets([my_asset])
        my_job = define_asset_job("asset_job").resolve(asset_graph=asset_graph)
        asset_key = AssetKey("my_asset")

        cached_status = get_and_update_asset_status_cache_value(
            created_instance, asset_key, asset_graph.get_partitions_def(asset_key)
        )
        failed_subset = cached_status.deserialize_failed_partition_subsets(
            asset_graph.get_partitions_def(asset_key)
        )
        assert failed_subset.get_partition_keys() == set()


def test_batch_canceled_partitions():
    my_asset = AssetKey("my_asset")

    # one more than the batch size to ensure we're hitting the pagination logic
    PARTITION_COUNT = RUN_FETCH_BATCH_SIZE + 1
    static_partitions_def = StaticPartitionsDefinition(
        [f"partition_{i}" for i in range(0, PARTITION_COUNT)]
    )
    run_ids_by_partition = {
        key: make_new_run_id() for key in static_partitions_def.get_partition_keys()
    }

    with instance_for_test() as instance:
        with create_and_delete_test_runs(instance, list(run_ids_by_partition.values())):
            for partition, run_id in run_ids_by_partition.items():
                instance.event_log_storage.store_event(
                    _create_test_planned_materialization_record(run_id, my_asset, partition)
                )

            failed_subset, in_progress_subset, _ = build_failed_and_in_progress_partition_subset(
                instance, my_asset, static_partitions_def, instance
            )
            assert failed_subset.get_partition_keys() == set()
            assert in_progress_subset.get_partition_keys() == set(
                static_partitions_def.get_partition_keys()
            )

            # cancel every run
            for run_id in run_ids_by_partition.values():
                run = instance.get_run_by_id(run_id)
                if run:
                    instance.report_run_canceled(run)

            failed_subset, in_progress_subset, _ = build_failed_and_in_progress_partition_subset(
                instance, my_asset, static_partitions_def, instance
            )
            assert failed_subset.get_partition_keys() == set()
            assert in_progress_subset.get_partition_keys() == set()


def _create_test_planned_materialization_record(run_id: str, asset_key: AssetKey, partition: str):
    return EventLogEntry(
        error_info=None,
        user_message="",
        level="debug",
        run_id=run_id,
        timestamp=time.time(),
        dagster_event=DagsterEvent(
            DagsterEventType.ASSET_MATERIALIZATION_PLANNED.value,
            "nonce",
            event_specific_data=AssetMaterializationPlannedData(
                asset_key=asset_key, partition=partition
            ),
        ),
    )
