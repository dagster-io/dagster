from typing import Optional, NamedTuple, Mapping
from dagster._serdes import (
    deserialize_json_to_dagster_namedtuple,
)
from collections import defaultdict
from dagster._serdes import whitelist_for_serdes
from dagster import _check as check
from dagster._core.definitions.partition import PartitionsSubset
from dagster import AssetKey, DagsterEventType, DagsterInstance, EventRecordsFilter
from dagster._core.definitions.asset_graph import AssetGraph
from dagster._core.definitions.partition import PartitionsDefinition
from dagster._core.definitions.multi_dimensional_partitions import (
    MultiPartitionsDefinition,
    get_multipartition_key_from_tags,
)


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

    def deserialize_materialized_partition_subsets(
        self, partitions_def: PartitionsDefinition
    ) -> PartitionsSubset:
        if not self.materialized_partition_subsets:
            return partitions_def.empty_subset()

        return partitions_def.deserialize_subset(self.materialized_partition_subsets)


def rebuild_materialized_partition_subset(
    instance: DagsterInstance,
    asset_key: AssetKey,
    latest_storage_id: int,
    partitions_def: Optional[PartitionsDefinition] = None,
):
    if not partitions_def:
        return AssetStatusCacheValue(latest_storage_id=latest_storage_id)

    if isinstance(partitions_def, MultiPartitionsDefinition):
        materialization_counts_by_partition = defaultdict(int)
        for event_tags in instance.get_event_tags_for_asset(asset_key):
            partition_key = get_multipartition_key_from_tags(event_tags)
            materialization_counts_by_partition[partition_key] += 1
    else:
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


def fetch_asset_status_cache_values_from_storage(
    instance: DagsterInstance, asset_key: Optional[AssetKey] = None
) -> Mapping[AssetKey, Optional[AssetStatusCacheValue]]:
    asset_records = (
        instance.get_asset_records()
        if not asset_key
        else instance.get_asset_records(asset_keys=[asset_key])
    )
    return {
        asset_record.asset_entry.asset_key: asset_record.asset_entry.cached_status
        for asset_record in asset_records
    }


def get_updated_asset_status_cache_values(
    instance: DagsterInstance,
    asset_graph: AssetGraph,
    asset_key: Optional[AssetKey] = None,  # If not provided, fetches all asset cache values
) -> Mapping[AssetKey, AssetStatusCacheValue]:
    cached_status_data_by_asset_key = fetch_asset_status_cache_values_from_storage(
        instance, asset_key
    )

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
    instance: DagsterInstance, asset_graph: AssetGraph, asset_key: Optional[AssetKey] = None
) -> Mapping[AssetKey, AssetStatusCacheValue]:
    updated_cache_values_by_asset_key = get_updated_asset_status_cache_values(
        instance, asset_graph, asset_key
    )
    for asset_key, status_cache_value in updated_cache_values_by_asset_key.items():
        instance.update_asset_cached_status_data(asset_key, status_cache_value)

    return updated_cache_values_by_asset_key
