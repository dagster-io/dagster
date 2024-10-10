from enum import Enum
from typing import TYPE_CHECKING, Iterable, List, NamedTuple, Optional, Sequence, Set, Tuple

from dagster import (
    AssetKey,
    DagsterInstance,
    DagsterRunStatus,
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
from dagster._core.loader import InstanceLoadableBy, LoadingContext
from dagster._core.storage.dagster_run import FINISHED_STATUSES, RunsFilter
from dagster._core.storage.tags import (
    MULTIDIMENSIONAL_PARTITION_PREFIX,
    get_dimension_from_partition_tag,
)
from dagster._serdes import whitelist_for_serdes
from dagster._serdes.errors import DeserializationError
from dagster._serdes.serdes import deserialize_value
from dagster._time import get_current_datetime

if TYPE_CHECKING:
    from dagster._core.storage.event_log.base import AssetRecord


CACHEABLE_PARTITION_TYPES = (
    TimeWindowPartitionsDefinition,
    MultiPartitionsDefinition,
    StaticPartitionsDefinition,
    DynamicPartitionsDefinition,
)
RUN_FETCH_BATCH_SIZE = 100


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
    ),
    InstanceLoadableBy[Tuple[AssetKey, PartitionsDefinition]],
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

    @classmethod
    def _blocking_batch_load(
        cls, keys: Iterable[Tuple[AssetKey, PartitionsDefinition]], instance: "DagsterInstance"
    ) -> Iterable[Optional["AssetStatusCacheValue"]]:
        partition_defs_by_key = {key: partition_def for key, partition_def in keys}
        return instance.event_log_storage.get_asset_status_cache_values(partition_defs_by_key)

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
        current_time = get_current_datetime()
        validated_partitions = {
            pk
            for pk in partition_keys
            if partitions_def.has_partition_key(pk, current_time=current_time)
        }
    return validated_partitions


def get_last_planned_storage_id(
    instance: DagsterInstance, asset_key: AssetKey, asset_record: Optional["AssetRecord"]
) -> int:
    if instance.event_log_storage.asset_records_have_last_planned_materialization_storage_id:
        return (
            (asset_record.asset_entry.last_planned_materialization_storage_id or 0)
            if asset_record
            else 0
        )

    info = instance.get_latest_planned_materialization_info(asset_key)
    if not info:
        return 0

    return info.storage_id


def _build_status_cache(
    instance: DagsterInstance,
    asset_key: AssetKey,
    partitions_def: Optional[PartitionsDefinition],
    dynamic_partitions_store: DynamicPartitionsStore,
    stored_cache_value: Optional[AssetStatusCacheValue],
    asset_record: Optional["AssetRecord"],
) -> Optional[AssetStatusCacheValue]:
    """This method refreshes the asset status cache for a given asset key. It recalculates
    the materialized partition subset for the asset key and updates the cache value.
    """
    last_materialization_storage_id = (
        asset_record.asset_entry.last_materialization_storage_id if asset_record else None
    )

    last_planned_materialization_storage_id = get_last_planned_storage_id(
        instance, asset_key, asset_record
    )

    latest_storage_id = max(
        last_materialization_storage_id or 0,
        last_planned_materialization_storage_id or 0,
    )
    if not latest_storage_id:
        return None

    if not partitions_def or not is_cacheable_partition_type(partitions_def):
        return AssetStatusCacheValue(latest_storage_id=latest_storage_id)

    failed_subset = (
        partitions_def.deserialize_subset(stored_cache_value.serialized_failed_partition_subset)
        if stored_cache_value and stored_cache_value.serialized_failed_partition_subset
        else None
    )

    cached_in_progress_cursor = (
        (
            stored_cache_value.earliest_in_progress_materialization_event_id - 1
            if stored_cache_value.earliest_in_progress_materialization_event_id
            else stored_cache_value.latest_storage_id
        )
        if stored_cache_value
        else None
    )

    if stored_cache_value:
        # fetch the incremental new materialized partitions, and update the cached materialized
        # subset
        new_partitions = set()
        if (
            last_materialization_storage_id
            and last_materialization_storage_id > stored_cache_value.latest_storage_id
        ):
            new_partitions = get_validated_partition_keys(
                dynamic_partitions_store,
                partitions_def,
                instance.get_materialized_partitions(
                    asset_key, after_cursor=stored_cache_value.latest_storage_id
                ),
            )

        materialized_subset: PartitionsSubset = (
            partitions_def.deserialize_subset(
                stored_cache_value.serialized_materialized_partition_subset
            )
            if stored_cache_value.serialized_materialized_partition_subset
            else partitions_def.empty_subset()
        )

        if new_partitions:
            materialized_subset = materialized_subset.with_partition_keys(new_partitions)

        if failed_subset and new_partitions:
            failed_subset = failed_subset - partitions_def.empty_subset().with_partition_keys(
                new_partitions
            )

    else:
        materialized_subset = partitions_def.empty_subset().with_partition_keys(
            get_validated_partition_keys(
                dynamic_partitions_store,
                partitions_def,
                instance.get_materialized_partitions(asset_key),
            )
        )

    (
        failed_subset,
        in_progress_subset,
        earliest_in_progress_materialization_event_id,
    ) = build_failed_and_in_progress_partition_subset(
        instance,
        asset_key,
        partitions_def,
        dynamic_partitions_store,
        last_planned_materialization_storage_id=last_planned_materialization_storage_id,
        failed_subset=failed_subset,
        after_storage_id=cached_in_progress_cursor,
    )

    return AssetStatusCacheValue(
        latest_storage_id=latest_storage_id,
        partitions_def_id=partitions_def.get_serializable_unique_identifier(
            dynamic_partitions_store=dynamic_partitions_store
        ),
        serialized_materialized_partition_subset=materialized_subset.serialize(),
        serialized_failed_partition_subset=failed_subset.serialize(),
        serialized_in_progress_partition_subset=in_progress_subset.serialize(),
        earliest_in_progress_materialization_event_id=earliest_in_progress_materialization_event_id,
    )


def build_failed_and_in_progress_partition_subset(
    instance: DagsterInstance,
    asset_key: AssetKey,
    partitions_def: PartitionsDefinition,
    dynamic_partitions_store: DynamicPartitionsStore,
    last_planned_materialization_storage_id: int,
    failed_subset: Optional[PartitionsSubset[str]] = None,
    after_storage_id: Optional[int] = None,
) -> Tuple[PartitionsSubset, PartitionsSubset, Optional[int]]:
    in_progress_partitions: Set[str] = set()

    incomplete_materializations = {}

    failed_subset = failed_subset or partitions_def.empty_subset()

    # Fetch incomplete materializations if there have been any planned materializations since the
    # cursor
    if last_planned_materialization_storage_id and (
        not after_storage_id or last_planned_materialization_storage_id > after_storage_id
    ):
        incomplete_materializations = instance.event_log_storage.get_latest_asset_partition_materialization_attempts_without_materializations(
            asset_key, after_storage_id=after_storage_id
        )

    failed_partitions: Set[str] = set()

    cursor = None
    if incomplete_materializations:
        to_fetch = list(set([run_id for run_id, _event_id in incomplete_materializations.values()]))
        finished_runs = {}
        unfinished_runs = {}

        while to_fetch:
            chunk = to_fetch[:RUN_FETCH_BATCH_SIZE]
            to_fetch = to_fetch[RUN_FETCH_BATCH_SIZE:]
            for r in instance.get_runs(filters=RunsFilter(run_ids=chunk)):
                if r.status in FINISHED_STATUSES:
                    finished_runs[r.run_id] = r.status
                else:
                    unfinished_runs[r.run_id] = r.status

        for partition, (run_id, event_id) in incomplete_materializations.items():
            if run_id in finished_runs:
                status = finished_runs.get(run_id)
                if status == DagsterRunStatus.FAILURE:
                    failed_partitions.add(partition)
            elif run_id in unfinished_runs:
                in_progress_partitions.add(partition)
                # If the run is not finished, keep track of the event id so we can check on it next time
                if cursor is None or event_id < cursor:
                    cursor = event_id
            else:
                # Runs that are neither finished nor unfinished must have been deleted, so are
                # considered neither in-progress nor failed
                pass

    if failed_partitions:
        failed_subset = failed_subset.with_partition_keys(
            get_validated_partition_keys(
                dynamic_partitions_store, partitions_def, failed_partitions
            )
        )

    return (
        failed_subset,
        (
            partitions_def.empty_subset().with_partition_keys(
                get_validated_partition_keys(instance, partitions_def, in_progress_partitions)
            )
            if in_progress_partitions
            else partitions_def.empty_subset()
        ),
        cursor,
    )


def get_and_update_asset_status_cache_value(
    instance: DagsterInstance,
    asset_key: AssetKey,
    partitions_def: Optional[PartitionsDefinition],
    dynamic_partitions_loader: Optional[DynamicPartitionsStore] = None,
    loading_context: Optional[LoadingContext] = None,
) -> Optional[AssetStatusCacheValue]:
    from dagster._core.storage.event_log.base import AssetRecord

    if loading_context:
        asset_record = AssetRecord.blocking_get(loading_context, asset_key)
    else:
        asset_record = next(iter(instance.get_asset_records(asset_keys=[asset_key])), None)

    if asset_record is None:
        stored_cache_value = None
    else:
        stored_cache_value = asset_record.asset_entry.cached_status

    dynamic_partitions_store = dynamic_partitions_loader if dynamic_partitions_loader else instance
    use_cached_value = (
        stored_cache_value
        and partitions_def
        and stored_cache_value.partitions_def_id
        == partitions_def.get_serializable_unique_identifier(
            dynamic_partitions_store=dynamic_partitions_store
        )
    )
    updated_cache_value = _build_status_cache(
        instance=instance,
        asset_key=asset_key,
        partitions_def=partitions_def,
        dynamic_partitions_store=dynamic_partitions_store,
        stored_cache_value=stored_cache_value if use_cached_value else None,
        asset_record=asset_record,
    )
    if (
        updated_cache_value is not None
        and instance.event_log_storage.can_write_asset_status_cache()
        and updated_cache_value != stored_cache_value
    ):
        instance.update_asset_cached_status_data(asset_key, updated_cache_value)

    return updated_cache_value
