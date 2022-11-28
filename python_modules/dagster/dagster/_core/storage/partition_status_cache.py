from typing import Optional, List, cast, Sequence, NamedTuple, Mapping
from dagster._serdes import (
    deserialize_as,
    deserialize_json_to_dagster_namedtuple,
    serialize_dagster_namedtuple,
)
from dagster._serdes import whitelist_for_serdes
from dagster._core.storage.event_log import EventLogRecord
from dagster import _check as check
from dagster._core.definitions.partition import PartitionsSubset
from dagster import AssetKey, DagsterEventType, DagsterInstance, EventRecordsFilter
from dagster._core.definitions.asset_graph import AssetGraph
from dagster._core.definitions.partition import PartitionsDefinition, PartitionKeyRange
from dagster._core.storage.event_log import AssetRecord

# from dagster._core.storage.event_log.sql_event_log import SqlEventLogStorage

# class PartitionSubsetCacheValue(
#     NamedTuple(
#         "_PartitionSubsetCacheValue", [("partition_subsets", str)]
#     )
# ):
#     def __new__(
#         cls,
#         partition_subsets: str,
#         # Is a different object than PartitionSubset to allow for future serializable values,
#         # e.g. a hash of the contained partition keys
#     ):
#         check.str_param(partition_subsets, "partition_subsets")
#         return super(PartitionSubsetCacheValue, cls).__new__(
#             cls, partition_subsets
#         )


@whitelist_for_serdes
class AssetStatusCacheValue(
    NamedTuple(
        "_AssetPartitionsStatusCacheValue",
        [
            ("latest_storage_id", int),
            ("partitions_def_id", Optional[str]),
            ("materialized_partition_subsets", Optional[str]),
            # Future partition subset features will go here, e.g. stale partition subsets
        ],
    )
):
    """
    Set of asset fields that reflect partition materialization status. This is used to display
    global partition status in the asset view.

    When recalculating:
        if partitions ID has changed, then need to recalculate. Could keep it simple and
        recalculate every time the partitions def changes, but if
    """

    def __new__(
        cls,
        latest_storage_id: int,
        partitions_def_id: Optional[str] = None,
        materialized_partition_subsets: Optional[str] = None,
    ):
        check.int_param(latest_storage_id, "latest_storage_id")
        check.opt_inst_param(
            materialized_partition_subsets,
            "materialized_partition_subsets",
            str,
        )
        check.opt_str_param(partitions_def_id, "partitions_def_id")
        return super(AssetStatusCacheValue, cls).__new__(
            cls, latest_storage_id, partitions_def_id, materialized_partition_subsets
        )

    @staticmethod
    def from_db_string(db_string):
        if not db_string:
            return None

        cached_data = deserialize_json_to_dagster_namedtuple(db_string)
        if not isinstance(cached_data, AssetStatusCacheValue):
            return None

        return cached_data


# def rebuild_partition_status_cache_value(
#     asset_key: AssetKey,
#     storage: SqlEventLogStorage,
#     partitions_def: Optional[PartitionsDefinition] = None,
# ):
#     materialized_subset = None
#     if partitions_def:
#         materialized_subset = partitions_def.empty_subset()
#         materialization_counts_by_partition = storage.get_materialization_count_by_partition(
#             [asset_key]
#         )
#         partition_keys = partitions_def.get_partition_keys()
#         materialized_keys = set(
#             materialization_counts_by_partition.get(asset_key, {}).keys()
#         ) & set(partition_keys)

#         materialized_subset.with_partition_keys(materialized_keys)
#     return materialized_subset


def rebuild_materialized_partition_subset(
    instance: DagsterInstance,
    asset_key: AssetKey,
    latest_storage_id: int,
    partitions_def: Optional[PartitionsDefinition] = None,
):
    if not partitions_def:
        return AssetStatusCacheValue(latest_storage_id=latest_storage_id)

    materialization_counts_by_partition = instance.get_materialization_count_by_partition(
        [asset_key]
    ).get(asset_key, {})
    materialized_partition_subsets = partitions_def.empty_subset()
    partition_keys = partitions_def.get_partition_keys()
    materialized_keys = set(materialization_counts_by_partition.keys()) & set(partition_keys)

    materialized_partition_subsets = materialized_partition_subsets.with_partition_keys(
        materialized_keys
    )

    return AssetStatusCacheValue(
        latest_storage_id=latest_storage_id,
        partitions_def_id=partitions_def.serializable_unique_identifier,
        materialized_partition_subsets=materialized_partition_subsets.serialize(),
    )


def get_updated_partition_status_cache_values(
    instance: DagsterInstance,
    asset_key: AssetKey,
    current_status_cache_value: AssetStatusCacheValue,
    partitions_def: Optional[PartitionsDefinition] = None,
):
    unevaluated_event_records = instance.get_event_records(
        event_records_filter=EventRecordsFilter(
            event_type=DagsterEventType.ASSET_MATERIALIZATION,
            asset_key=asset_key,
            after_cursor=current_status_cache_value.latest_storage_id
            if current_status_cache_value
            else None,
        )
    )

    if not unevaluated_event_records:
        return current_status_cache_value

    latest_storage_id = max([record.storage_id for record in unevaluated_event_records])
    if not partitions_def:
        return AssetStatusCacheValue(latest_storage_id=latest_storage_id)

    check.invariant(
        current_status_cache_value.partitions_def_id
        == partitions_def.serializable_unique_identifier
    )
    materialized_subset: PartitionsSubset = (
        partitions_def.deserialize_subset(current_status_cache_value.materialized_partition_subsets)
        if current_status_cache_value and current_status_cache_value.materialized_partition_subsets
        else partitions_def.empty_subset()
    )
    newly_materialized_partitions = set()

    for unevaluated_materializations in unevaluated_event_records:
        if not (
            unevaluated_materializations.event_log_entry.dagster_event
            and unevaluated_materializations.event_log_entry.dagster_event.is_step_materialization
        ):
            check.failed("Expected materialization event")
        newly_materialized_partitions.add(
            unevaluated_materializations.event_log_entry.dagster_event.partition
        )
    materialized_subset = materialized_subset.with_partition_keys(newly_materialized_partitions)
    return AssetStatusCacheValue(
        latest_storage_id=latest_storage_id,
        partitions_def_id=current_status_cache_value.partitions_def_id,
        materialized_partition_subsets=materialized_subset.serialize(),
    )


def get_updated_asset_status_cache_values(
    instance: DagsterInstance,
    asset_graph: AssetGraph,
) -> Mapping[AssetKey, AssetStatusCacheValue]:

    asset_records = instance.get_asset_records()
    cached_status_data_by_asset_key = {
        asset_record.asset_entry.asset_key: asset_record.asset_entry.cached_status
        for asset_record in asset_records
    }

    updated_cache_values_by_asset_key = {}
    for asset_key, cached_status_data in cached_status_data_by_asset_key.items():
        if asset_key not in asset_graph.all_asset_keys:
            # Do not calculate new value if asset not in graph
            continue

        partitions_def = asset_graph.get_partitions_def(asset_key)
        if cached_status_data is None or cached_status_data.partitions_def_id != (
            partitions_def.serializable_unique_identifier if partitions_def else None
        ):
            event_records = instance.get_event_records(
                event_records_filter=EventRecordsFilter(
                    event_type=DagsterEventType.ASSET_MATERIALIZATION,
                    asset_key=asset_key,
                ),
                limit=1,
            )
            if event_records:
                updated_cache_values_by_asset_key[
                    asset_key
                ] = rebuild_materialized_partition_subset(
                    instance=instance,
                    asset_key=asset_key,
                    partitions_def=partitions_def,
                    latest_storage_id=next(iter(event_records)).storage_id,
                )
        else:
            updated_cache_values_by_asset_key[
                asset_key
            ] = get_updated_partition_status_cache_values(
                instance=instance,
                asset_key=asset_key,
                partitions_def=partitions_def,
                current_status_cache_value=cached_status_data,
            )

    return updated_cache_values_by_asset_key


def update_asset_status_cache_values(
    instance: DagsterInstance,
    asset_graph: AssetGraph,
) -> None:
    for asset_key, status_cache_value in get_updated_asset_status_cache_values(
        instance, asset_graph
    ).items():
        instance.update_asset_cached_status_data(asset_key, status_cache_value)


# def get_materialized_partition_ranges(
#     instance: DagsterInstance,
#     asset_graph: AssetGraph,
#     asset_key: AssetKey,
# ) -> List[PartitionKeyRange]:
#     partitions_def = asset_graph.get_partitions_def(asset_key)
#     if partitions_def is None:
#         return []
#     partition_keys = partitions_def.get_partition_keys()

#     latest_storage_id = None
#     materialized_subset: PartitionsSubset = partitions_def.empty_subset()

#     asset_key_str = cast(str, asset_key.to_string())
#     serialized_cache_value = instance.run_storage.kvs_get(set(asset_key_str)).get(asset_key_str, "")
#     # TODO: assert that partitions_def_id is the same
#     if serialized_cache_value:
#         cache_value = cast(
#             AssetStatusCacheValue,
#             deserialize_json_to_dagster_namedtuple(serialized_cache_value),
#         )

#         # Call get_updated_asset_status_cache_value

#     new_materialization_records = instance.get_event_records(
#         EventRecordsFilter(
#             event_type=DagsterEventType.ASSET_MATERIALIZATION,
#             asset_key=asset_key,
#             after_cursor=latest_storage_id,
#         )
#     )

#     new_materialization_partitions = {
#         cast(str, record.partition_key)
#         for record in new_materialization_records
#         if record.partition_key in partition_keys
#     }
#     max_storage_id = max(
#         (record.storage_id for record in new_materialization_records), default=latest_storage_id
#     )
#     updated_materialized_subset = materialized_subset.with_partition_keys(
#         new_materialization_partitions
#     )

#     if max_storage_id:  # If nonexistent, asset has not been materialized
#         instance.run_storage.kvs_set(
#             {
#                 asset_key_str: serialize_dagster_namedtuple(
#                     AssetStatusCacheValue(
#                         latest_storage_id=max_storage_id,
#                         partitions_def_id=partitions_def.serializable_unique_identifier,
#                         materialized_partition_subsets=updated_materialized_subset.serialize(),
#                     )
#                 ),
#             }
#         )

#     # return updated_materialized_subset.key_ranges
