from enum import Enum
from typing import TYPE_CHECKING, Dict, List, NamedTuple, Optional, Sequence, Set, Tuple

from dagster import (
    AssetKey,
    DagsterEventType,
    DagsterInstance,
    DagsterRunStatus,
    EventLogRecord,
    EventRecordsFilter,
    _check as check,
)
from dagster._core.definitions.multi_dimensional_partitions import (
    MultiPartitionKey,
    MultiPartitionsDefinition,
)
from dagster._core.definitions.partition import (
    DynamicPartitionsDefinition,
    PartitionsDefinition,
    PartitionsSubset,
    StaticPartitionsDefinition,
)
from dagster._core.definitions.time_window_partitions import TimeWindowPartitionsDefinition
from dagster._core.instance import DynamicPartitionsStore
from dagster._core.storage.dagster_run import FINISHED_STATUSES, RunsFilter
from dagster._core.storage.tags import (
    MULTIDIMENSIONAL_PARTITION_PREFIX,
    get_dimension_from_partition_tag,
)
from dagster._serdes import whitelist_for_serdes
from dagster._serdes.errors import DeserializationError
from dagster._serdes.serdes import deserialize_value

if TYPE_CHECKING:
    from dagster._core.storage.event_log.base import AssetRecord


CACHEABLE_PARTITION_TYPES = (
    TimeWindowPartitionsDefinition,
    MultiPartitionsDefinition,
    StaticPartitionsDefinition,
    DynamicPartitionsDefinition,
)


class AssetPartitionStatus(Enum):
    """The status of asset partition."""

    MATERIALIZED = "MATERIALIZED"
    IN_PROGRESS = "IN_PROGRESS"
    FAILED = "FAILED"


def is_cacheable_partition_type(partitions_def: PartitionsDefinition) -> bool:
    check.inst_param(partitions_def, "partitions_def", PartitionsDefinition)
    if not isinstance(partitions_def, CACHEABLE_PARTITION_TYPES):
        return False
    if isinstance(partitions_def, MultiPartitionsDefinition):
        return all(
            is_cacheable_partition_type(dimension_def.partitions_def)
            for dimension_def in partitions_def.partitions_defs
        )
    return (
        partitions_def.name is not None
        if isinstance(partitions_def, DynamicPartitionsDefinition)
        else True
    )


@whitelist_for_serdes
class AssetStatusCacheValue(
    NamedTuple(
        "_AssetPartitionsStatusCacheValue",
        [
            ("latest_storage_id", int),
            ("partitions_def_id", Optional[str]),
            ("serialized_materialized_partition_subset", Optional[str]),
            ("serialized_failed_partition_subset", Optional[str]),
            ("serialized_in_progress_partition_subset", Optional[str]),
            ("earliest_in_progress_materialization_event_id", Optional[int]),
        ],
    )
):
    """Set of asset fields that reflect partition materialization status. This is used to display
    global partition status in the asset view.

    Properties:
        latest_storage_id (int): The latest evaluated storage id for the asset.
        partitions_def_id (Optional(str)): The serializable unique identifier for the partitions
            definition. When this value differs from the new partitions definition, this cache
            value needs to be recalculated. None if the asset is unpartitioned.
        serialized_materialized_partition_subset (Optional(str)): The serialized representation of the
            materialized partition subsets, up to the latest storage id. None if the asset is
            unpartitioned.
        serialized_failed_partition_subset (Optional(str)): The serialized representation of the failed
            partition subsets, up to the latest storage id. None if the asset is unpartitioned.
        serialized_in_progress_partition_subset (Optional(str)): The serialized representation of the
            in progress partition subsets, up to the latest storage id. None if the asset is unpartitioned.
        earliest_in_progress_materialization_event_id (Optional(int)): The event id of the earliest
            materialization planned event for a run that is still in progress. This is used to check
            on the status of runs that are still in progress.
    """

    def __new__(
        cls,
        latest_storage_id: int,
        partitions_def_id: Optional[str] = None,
        serialized_materialized_partition_subset: Optional[str] = None,
        serialized_failed_partition_subset: Optional[str] = None,
        serialized_in_progress_partition_subset: Optional[str] = None,
        earliest_in_progress_materialization_event_id: Optional[int] = None,
    ):
        check.int_param(latest_storage_id, "latest_storage_id")
        check.opt_str_param(partitions_def_id, "partitions_def_id")
        check.opt_str_param(
            serialized_materialized_partition_subset, "serialized_materialized_partition_subset"
        )
        check.opt_str_param(
            serialized_failed_partition_subset, "serialized_failed_partition_subset"
        )
        check.opt_str_param(
            serialized_in_progress_partition_subset, "serialized_in_progress_partition_subset"
        )
        return super(AssetStatusCacheValue, cls).__new__(
            cls,
            latest_storage_id,
            partitions_def_id,
            serialized_materialized_partition_subset,
            serialized_failed_partition_subset,
            serialized_in_progress_partition_subset,
            earliest_in_progress_materialization_event_id,
        )

    @staticmethod
    def from_db_string(db_string: str) -> Optional["AssetStatusCacheValue"]:
        if not db_string:
            return None

        try:
            cached_data = deserialize_value(db_string, AssetStatusCacheValue)
        except DeserializationError:
            return None

        return cached_data

    def deserialize_materialized_partition_subsets(
        self, partitions_def: PartitionsDefinition
    ) -> PartitionsSubset:
        if not self.serialized_materialized_partition_subset:
            return partitions_def.empty_subset()

        return partitions_def.deserialize_subset(self.serialized_materialized_partition_subset)

    def deserialize_failed_partition_subsets(
        self, partitions_def: PartitionsDefinition
    ) -> PartitionsSubset:
        if not self.serialized_failed_partition_subset:
            return partitions_def.empty_subset()

        return partitions_def.deserialize_subset(self.serialized_failed_partition_subset)

    def deserialize_in_progress_partition_subsets(
        self, partitions_def: PartitionsDefinition
    ) -> PartitionsSubset:
        if not self.serialized_in_progress_partition_subset:
            return partitions_def.empty_subset()

        return partitions_def.deserialize_subset(self.serialized_in_progress_partition_subset)


def get_materialized_multipartitions(
    instance: DagsterInstance, asset_key: AssetKey, partitions_def: MultiPartitionsDefinition
) -> Sequence[str]:
    dimension_names = partitions_def.partition_dimension_names
    materialized_keys: List[MultiPartitionKey] = []
    for event_tags in instance.get_event_tags_for_asset(asset_key):
        event_partition_keys_by_dimension = {
            get_dimension_from_partition_tag(key): value
            for key, value in event_tags.items()
            if key.startswith(MULTIDIMENSIONAL_PARTITION_PREFIX)
        }

        if all(
            dimension_name in event_partition_keys_by_dimension.keys()
            for dimension_name in dimension_names
        ):
            materialized_keys.append(
                MultiPartitionKey(
                    {
                        dimension_names[0]: event_partition_keys_by_dimension[dimension_names[0]],
                        dimension_names[1]: event_partition_keys_by_dimension[dimension_names[1]],
                    }
                )
            )
    return materialized_keys


def get_validated_partition_keys(
    dynamic_partitions_store: DynamicPartitionsStore,
    partitions_def: PartitionsDefinition,
    partition_keys: Set[str],
):
    if isinstance(partitions_def, (DynamicPartitionsDefinition, StaticPartitionsDefinition)):
        validated_partitions = (
            set(
                partitions_def.get_partition_keys(dynamic_partitions_store=dynamic_partitions_store)
            )
            & partition_keys
        )
    elif isinstance(partitions_def, MultiPartitionsDefinition):
        validated_partitions = partitions_def.filter_valid_partition_keys(
            partition_keys, dynamic_partitions_store
        )
    else:
        if not isinstance(partitions_def, TimeWindowPartitionsDefinition):
            check.failed("Unexpected partitions definition type {partitions_def}")
        validated_partitions = {
            pk for pk in partition_keys if partitions_def.is_valid_partition_key(pk)
        }
    return validated_partitions


def _build_status_cache(
    instance: DagsterInstance,
    asset_key: AssetKey,
    latest_storage_id: int,
    partitions_def: Optional[PartitionsDefinition],
    dynamic_partitions_store: DynamicPartitionsStore,
) -> AssetStatusCacheValue:
    """This method refreshes the asset status cache for a given asset key. It recalculates
    the materialized partition subset for the asset key and updates the cache value.
    """
    if not partitions_def or not is_cacheable_partition_type(partitions_def):
        return AssetStatusCacheValue(latest_storage_id=latest_storage_id)

    materialized_keys: Sequence[str]
    if isinstance(partitions_def, MultiPartitionsDefinition):
        materialized_keys = get_materialized_multipartitions(instance, asset_key, partitions_def)
    else:
        materialized_keys = [
            key
            for key, count in instance.get_materialization_count_by_partition([asset_key])
            .get(asset_key, {})
            .items()
            if count > 0
        ]

    serialized_materialized_partition_subset = partitions_def.empty_subset()

    serialized_materialized_partition_subset = (
        serialized_materialized_partition_subset.with_partition_keys(
            get_validated_partition_keys(
                dynamic_partitions_store, partitions_def, set(materialized_keys)
            )
        )
    )

    failed_subset, in_progress_subset, cursor = build_failed_and_in_progress_partition_subset(
        instance, asset_key, partitions_def, dynamic_partitions_store
    )

    return AssetStatusCacheValue(
        latest_storage_id=latest_storage_id,
        partitions_def_id=partitions_def.get_serializable_unique_identifier(
            dynamic_partitions_store=dynamic_partitions_store
        ),
        serialized_materialized_partition_subset=serialized_materialized_partition_subset.serialize(),
        serialized_failed_partition_subset=failed_subset.serialize(),
        serialized_in_progress_partition_subset=in_progress_subset.serialize(),
        earliest_in_progress_materialization_event_id=cursor,
    )


def build_failed_and_in_progress_partition_subset(
    instance: DagsterInstance,
    asset_key: AssetKey,
    partitions_def: PartitionsDefinition,
    dynamic_partitions_store: DynamicPartitionsStore,
) -> Tuple[PartitionsSubset, PartitionsSubset, Optional[int]]:
    incomplete_materializations = instance.event_log_storage.get_latest_asset_partition_materialization_attempts_without_materializations(
        asset_key
    )

    if not incomplete_materializations:
        return partitions_def.empty_subset(), partitions_def.empty_subset(), None

    finished_runs = {
        r.run_id: r.status
        for r in instance.get_runs(
            filters=RunsFilter(
                run_ids=[run_id for run_id, _event_id in incomplete_materializations.values()],
                statuses=FINISHED_STATUSES,
            )
        )
    }

    new_failed_partitions = set()
    in_progress_partitions = set()
    cursor = None
    for partition, (run_id, event_id) in incomplete_materializations.items():
        if run_id in finished_runs:
            status = finished_runs.get(run_id)
            if status == DagsterRunStatus.FAILURE:
                new_failed_partitions.add(partition)
        else:
            in_progress_partitions.add(partition)
            # If the run is not finished, keep track of the event id so we can check on it next time
            if cursor is None or event_id < cursor:
                cursor = event_id

    return (
        partitions_def.empty_subset().with_partition_keys(
            get_validated_partition_keys(
                dynamic_partitions_store, partitions_def, new_failed_partitions
            )
        )
        if new_failed_partitions
        else partitions_def.empty_subset(),
        partitions_def.empty_subset().with_partition_keys(
            get_validated_partition_keys(instance, partitions_def, in_progress_partitions)
        )
        if in_progress_partitions
        else partitions_def.empty_subset(),
        cursor,
    )


def _get_updated_failed_and_in_progress_partition_subset(
    instance: DagsterInstance,
    asset_key: AssetKey,
    partitions_def: PartitionsDefinition,
    current_cached_subset: PartitionsSubset,
    unevaluated_event_records: Sequence[EventLogRecord],
    dynamic_partitions_store: DynamicPartitionsStore,
) -> Tuple[PartitionsSubset, PartitionsSubset, Optional[int]]:
    current_failed_partitions = set(current_cached_subset.get_partition_keys())

    cursor = None
    incomplete_materialization_records: Dict[str, EventLogRecord] = {}
    for record in sorted(unevaluated_event_records, key=lambda r: r.storage_id):
        event = check.not_none(record.event_log_entry.dagster_event)
        if event.is_asset_materialization_planned:
            if event.partition:
                # If we have a planned materilization for a partition, keep track of it to see if we
                # also find a materialization. If not, we'll check if the run failed and add it to
                # the failed partitions.
                incomplete_materialization_records[event.partition] = record
        if event.is_step_materialization:
            if event.partition:
                incomplete_materialization_records.pop(event.partition, None)
                # if we have a new materialization for a partition, that negates the old failure
                current_failed_partitions.discard(event.partition)

    new_failed_partitions = set()
    in_progress_partitions = set()
    if incomplete_materialization_records:
        finished_runs = {
            r.run_id: r.status
            for r in instance.get_runs(
                filters=RunsFilter(
                    run_ids=[
                        record.run_id for record in incomplete_materialization_records.values()
                    ],
                    statuses=FINISHED_STATUSES,
                )
            )
        }

        for partition, record in incomplete_materialization_records.items():
            if record.run_id in finished_runs:
                if finished_runs[record.run_id] == DagsterRunStatus.FAILURE:
                    new_failed_partitions.add(partition)
            else:
                in_progress_partitions.add(partition)
                if cursor is None or record.storage_id <= cursor:
                    # If the run is not finished, keep track of the event id so we can check on it next time
                    cursor = record.storage_id

    return (
        partitions_def.empty_subset().with_partition_keys(
            get_validated_partition_keys(
                instance, partitions_def, new_failed_partitions | current_failed_partitions
            )
        ),
        partitions_def.empty_subset().with_partition_keys(
            get_validated_partition_keys(instance, partitions_def, in_progress_partitions)
        ),
        cursor,
    )


def _get_updated_status_cache(
    instance: DagsterInstance,
    asset_key: AssetKey,
    stored_cache_value: AssetStatusCacheValue,
    partitions_def: Optional[PartitionsDefinition],
    dynamic_partitions_store: DynamicPartitionsStore,
    latest_materialization_storage_id: Optional[int],
) -> AssetStatusCacheValue:
    """This method accepts the current asset status cache value, and fetches unevaluated
    records from the event log. It then updates the cache value with the new materializations.
    """
    # if earliest_in_progress_materialization_event_id is set, we fetch all events including the
    # materialization planned event at that id (hence the - 1). We'll use this to determine if the
    # materialization is still in progress.
    cursor = (
        stored_cache_value.earliest_in_progress_materialization_event_id - 1
        if stored_cache_value.earliest_in_progress_materialization_event_id
        else stored_cache_value.latest_storage_id
    )
    unevaluated_planned_event_records = instance.get_event_records(
        event_records_filter=EventRecordsFilter(
            event_type=DagsterEventType.ASSET_MATERIALIZATION_PLANNED,
            asset_key=asset_key,
            after_cursor=cursor,
        )
    )
    unevaluated_materialization_event_records = (
        instance.get_event_records(
            event_records_filter=EventRecordsFilter(
                event_type=DagsterEventType.ASSET_MATERIALIZATION,
                asset_key=asset_key,
                after_cursor=cursor,
            )
        )
        if cursor < (latest_materialization_storage_id or 0)
        else []
    )

    if not (unevaluated_materialization_event_records or unevaluated_planned_event_records):
        return stored_cache_value

    unevaluated_event_records = list(unevaluated_planned_event_records)
    unevaluated_event_records.extend(list(unevaluated_materialization_event_records))

    latest_storage_id = max([record.storage_id for record in unevaluated_event_records])
    if not partitions_def or not is_cacheable_partition_type(partitions_def):
        return AssetStatusCacheValue(latest_storage_id=latest_storage_id)

    check.invariant(
        stored_cache_value.partitions_def_id
        == partitions_def.get_serializable_unique_identifier(
            dynamic_partitions_store=dynamic_partitions_store
        )
    )
    materialized_subset: PartitionsSubset = (
        partitions_def.deserialize_subset(
            stored_cache_value.serialized_materialized_partition_subset
        )
        if stored_cache_value and stored_cache_value.serialized_materialized_partition_subset
        else partitions_def.empty_subset()
    )
    newly_materialized_partitions = set()

    for record in unevaluated_event_records:
        if not record.event_log_entry.dagster_event:
            check.failed("Expected dagster event")

        if record.event_log_entry.dagster_event.is_step_materialization:
            if record.event_log_entry.dagster_event.partition:
                newly_materialized_partitions.add(record.event_log_entry.dagster_event.partition)
        elif not record.event_log_entry.dagster_event.is_asset_materialization_planned:
            check.failed("Expected materialization or materialization planned event")

    materialized_subset = materialized_subset.with_partition_keys(
        get_validated_partition_keys(
            dynamic_partitions_store, partitions_def, newly_materialized_partitions
        )
    )

    failed_subset: PartitionsSubset = (
        partitions_def.deserialize_subset(stored_cache_value.serialized_failed_partition_subset)
        if stored_cache_value and stored_cache_value.serialized_failed_partition_subset
        else partitions_def.empty_subset()
    )

    (
        failed_subset,
        in_progress_subset,
        new_cursor,
    ) = _get_updated_failed_and_in_progress_partition_subset(
        instance,
        asset_key,
        partitions_def,
        failed_subset,
        unevaluated_event_records,
        dynamic_partitions_store=dynamic_partitions_store,
    )

    return AssetStatusCacheValue(
        latest_storage_id=latest_storage_id,
        partitions_def_id=stored_cache_value.partitions_def_id,
        serialized_materialized_partition_subset=materialized_subset.serialize(),
        serialized_failed_partition_subset=failed_subset.serialize(),
        serialized_in_progress_partition_subset=in_progress_subset.serialize(),
        earliest_in_progress_materialization_event_id=new_cursor,
    )


def _get_fresh_asset_status_cache_value(
    instance: DagsterInstance,
    asset_key: AssetKey,
    dynamic_partitions_store: DynamicPartitionsStore,
    partitions_def: Optional[PartitionsDefinition],
    stored_cache_value: Optional[AssetStatusCacheValue],
    latest_materialization_storage_id: Optional[int],
) -> Optional[AssetStatusCacheValue]:
    updated_cache_value = None
    if stored_cache_value is None or stored_cache_value.partitions_def_id != (
        partitions_def.get_serializable_unique_identifier(
            dynamic_partitions_store=dynamic_partitions_store
        )
        if partitions_def
        else None
    ):
        planned_event_records = instance.get_event_records(
            event_records_filter=EventRecordsFilter(
                event_type=DagsterEventType.ASSET_MATERIALIZATION_PLANNED,
                asset_key=asset_key,
            ),
            limit=1,
        )

        if latest_materialization_storage_id or planned_event_records:
            latest_storage_id = max(
                (latest_materialization_storage_id or 0),
                next(iter(planned_event_records)).storage_id if planned_event_records else 0,
            )
            updated_cache_value = _build_status_cache(
                instance=instance,
                asset_key=asset_key,
                partitions_def=partitions_def,
                latest_storage_id=latest_storage_id,
                dynamic_partitions_store=dynamic_partitions_store,
            )
    else:
        updated_cache_value = _get_updated_status_cache(
            instance=instance,
            asset_key=asset_key,
            partitions_def=partitions_def,
            stored_cache_value=stored_cache_value,
            dynamic_partitions_store=dynamic_partitions_store,
            latest_materialization_storage_id=latest_materialization_storage_id,
        )

    return updated_cache_value


def get_and_update_asset_status_cache_value(
    instance: DagsterInstance,
    asset_key: AssetKey,
    partitions_def: Optional[PartitionsDefinition] = None,
    dynamic_partitions_loader: Optional[DynamicPartitionsStore] = None,
    asset_record: Optional["AssetRecord"] = None,
) -> Optional[AssetStatusCacheValue]:
    asset_record = asset_record or next(
        iter(instance.get_asset_records(asset_keys=[asset_key])), None
    )
    if asset_record is None:
        stored_cache_value, latest_materialization_storage_id = None, None
    else:
        stored_cache_value = asset_record.asset_entry.cached_status
        latest_materialization_storage_id = asset_record.asset_entry.last_materialization_storage_id

    updated_cache_value = _get_fresh_asset_status_cache_value(
        instance=instance,
        asset_key=asset_key,
        partitions_def=partitions_def,
        dynamic_partitions_store=dynamic_partitions_loader
        if dynamic_partitions_loader
        else instance,
        stored_cache_value=stored_cache_value,
        latest_materialization_storage_id=latest_materialization_storage_id,
    )
    if updated_cache_value is not None and updated_cache_value != stored_cache_value:
        instance.update_asset_cached_status_data(asset_key, updated_cache_value)

    return updated_cache_value
