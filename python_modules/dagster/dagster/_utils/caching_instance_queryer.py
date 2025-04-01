import logging
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from datetime import datetime
from typing import TYPE_CHECKING, AbstractSet, Optional, Union, cast  # noqa: UP035

import dagster._check as check
from dagster._core.asset_graph_view.serializable_entity_subset import SerializableEntitySubset
from dagster._core.definitions.asset_graph_subset import AssetGraphSubset
from dagster._core.definitions.base_asset_graph import BaseAssetGraph
from dagster._core.definitions.data_version import DataVersion, extract_data_version_from_entry
from dagster._core.definitions.declarative_automation.legacy.valid_asset_subset import (
    ValidAssetSubset,
)
from dagster._core.definitions.events import AssetKey, AssetKeyPartitionKey
from dagster._core.definitions.partition import PartitionsDefinition, PartitionsSubset
from dagster._core.definitions.time_window_partitions import (
    TimeWindowPartitionsDefinition,
    get_time_partition_key,
    get_time_partitions_def,
)
from dagster._core.errors import (
    DagsterDefinitionChangedDeserializationError,
    DagsterInvalidDefinitionError,
)
from dagster._core.event_api import AssetRecordsFilter
from dagster._core.events import DagsterEventType
from dagster._core.instance import DagsterInstance, DynamicPartitionsStore
from dagster._core.loader import LoadingContext
from dagster._core.storage.dagster_run import (
    IN_PROGRESS_RUN_STATUSES,
    DagsterRun,
    DagsterRunStatus,
    RunRecord,
)
from dagster._core.storage.tags import PARTITION_NAME_TAG
from dagster._time import get_current_datetime
from dagster._utils.cached_method import cached_method

if TYPE_CHECKING:
    from dagster._core.execution.asset_backfill import AssetBackfillData
    from dagster._core.storage.event_log import EventLogRecord
    from dagster._core.storage.event_log.base import AssetRecord
    from dagster._core.storage.partition_status_cache import AssetStatusCacheValue

RECORD_BATCH_SIZE = 1000


class CachingInstanceQueryer(DynamicPartitionsStore):
    """Provides utility functions for querying for asset-materialization related data from the
    instance which will attempt to limit redundant expensive calls. Intended for use within the
    scope of a single "request" (e.g. GQL request, sensor tick).

    Args:
        instance (DagsterInstance): The instance to query.
    """

    def __init__(
        self,
        instance: DagsterInstance,
        asset_graph: BaseAssetGraph,
        loading_context: LoadingContext,
        evaluation_time: Optional[datetime] = None,
        logger: Optional[logging.Logger] = None,
    ):
        self._instance = instance
        self._loading_context = loading_context

        self._asset_graph = asset_graph
        self._logger = logger or logging.getLogger("dagster")

        self._asset_partitions_cache: dict[Optional[int], dict[AssetKey, set[str]]] = defaultdict(
            dict
        )
        self._asset_partition_versions_updated_after_cursor_cache: dict[
            AssetKeyPartitionKey, int
        ] = {}

        self._dynamic_partitions_cache: dict[str, Sequence[str]] = {}

        self._evaluation_time = evaluation_time if evaluation_time else get_current_datetime()

        self._respect_materialization_data_versions = (
            self._instance.auto_materialize_respect_materialization_data_versions
        )

    @property
    def instance(self) -> DagsterInstance:
        return self._instance

    @property
    def asset_graph(self) -> BaseAssetGraph:
        return self._asset_graph

    @property
    def evaluation_time(self) -> datetime:
        return self._evaluation_time

    ####################
    # QUERY BATCHING
    ####################

    def prefetch_asset_records(self, asset_keys: Iterable[AssetKey]):
        """For performance, batches together queries for selected assets."""
        from dagster._core.storage.event_log.base import AssetRecord

        AssetRecord.blocking_get_many(self._loading_context, asset_keys)

    ####################
    # ASSET STATUS CACHE
    ####################

    @cached_method
    def _get_updated_cache_value(self, *, asset_key: AssetKey) -> Optional["AssetStatusCacheValue"]:
        from dagster._core.storage.partition_status_cache import (
            get_and_update_asset_status_cache_value,
        )

        partitions_def = check.not_none(self.asset_graph.get(asset_key).partitions_def)
        return get_and_update_asset_status_cache_value(
            instance=self.instance,
            asset_key=asset_key,
            partitions_def=partitions_def,
            dynamic_partitions_loader=self,
            loading_context=self._loading_context,
        )

    @cached_method
    def get_failed_or_in_progress_subset(self, *, asset_key: AssetKey) -> PartitionsSubset:
        """Returns a PartitionsSubset representing the set of partitions that are either in progress
        or whose last materialization attempt failed.
        """
        partitions_def = check.not_none(self.asset_graph.get(asset_key).partitions_def)
        cache_value = self._get_updated_cache_value(asset_key=asset_key)
        if cache_value is None:
            return partitions_def.empty_subset()

        return cache_value.deserialize_failed_partition_subsets(
            partitions_def
        ) | cache_value.deserialize_in_progress_partition_subsets(partitions_def)

    @cached_method
    def get_materialized_asset_subset(
        self, *, asset_key: AssetKey
    ) -> SerializableEntitySubset[AssetKey]:
        """Returns an AssetSubset representing the subset of the asset that has been materialized."""
        partitions_def = self.asset_graph.get(asset_key).partitions_def
        if partitions_def:
            cache_value = self._get_updated_cache_value(asset_key=asset_key)
            if cache_value is None:
                value = partitions_def.empty_subset()
            else:
                value = cache_value.deserialize_materialized_partition_subsets(partitions_def)
        else:
            value = self.asset_partition_has_materialization_or_observation(
                AssetKeyPartitionKey(asset_key)
            )
        return SerializableEntitySubset(key=asset_key, value=value)

    @cached_method
    def get_in_progress_asset_subset(
        self, *, asset_key: AssetKey
    ) -> SerializableEntitySubset[AssetKey]:
        """Returns an AssetSubset representing the subset of the asset that is currently in progress."""
        partitions_def = self.asset_graph.get(asset_key).partitions_def
        if partitions_def:
            cache_value = self._get_updated_cache_value(asset_key=asset_key)
            if cache_value is None:
                value = partitions_def.empty_subset()
            else:
                value = cache_value.deserialize_in_progress_partition_subsets(partitions_def)
        else:
            # NOTE: this computation is not correct in all cases for unpartitioned assets. it is
            # possible (though rare) for run A to be launched targeting an asset, then later run B
            # be launched, and then run B completes before run A. In these cases, the computation
            # below will consider the asset to not be in progress, as the latest planned event
            # will be associated with a completed run.
            asset_record = self.get_asset_record(asset_key)
            last_materialized_run_id = (
                asset_record.asset_entry.last_materialization_record.run_id
                if asset_record and asset_record.asset_entry.last_materialization_record
                else None
            )

            planned_materialization_run_id = None
            if self.instance.event_log_storage.asset_records_have_last_planned_and_failed_materializations:
                planned_materialization_run_id = (
                    asset_record.asset_entry.last_planned_materialization_run_id
                    if asset_record
                    else None
                )
            else:
                planned_materialization_info = (
                    self.instance.event_log_storage.get_latest_planned_materialization_info(
                        asset_key
                    )
                )
                planned_materialization_run_id = (
                    planned_materialization_info.run_id if planned_materialization_info else None
                )
            if (
                not planned_materialization_run_id
                # if the latest materialization happened in the same run as the latest planned materialization,
                # it's no longer in progress
                or last_materialized_run_id == planned_materialization_run_id
            ):
                value = False
            else:
                dagster_run = self.instance.get_run_by_id(planned_materialization_run_id)
                value = dagster_run is not None and dagster_run.status in [
                    *IN_PROGRESS_RUN_STATUSES,
                    # an asset is considered to be "in progress" if there is planned work for it that has not
                    # yet completed, which is not identical to the "in progress" status of the run
                    DagsterRunStatus.QUEUED,
                ]

        return SerializableEntitySubset(key=asset_key, value=value)

    @cached_method
    def get_failed_asset_subset(self, *, asset_key: AssetKey) -> SerializableEntitySubset[AssetKey]:
        """Returns an AssetSubset representing the subset of the asset that failed to be
        materialized its most recent run.
        """
        partitions_def = self.asset_graph.get(asset_key).partitions_def
        if partitions_def:
            cache_value = self._get_updated_cache_value(asset_key=asset_key)
            if cache_value is None:
                value = partitions_def.empty_subset()
            else:
                value = cache_value.deserialize_failed_partition_subsets(partitions_def)
        else:
            # ideally, unpartitioned assets would also be handled by the asset status cache
            planned_materialization_info = (
                self.instance.event_log_storage.get_latest_planned_materialization_info(asset_key)
            )
            if not planned_materialization_info:
                value = False
            else:
                dagster_run = self.instance.get_run_by_id(planned_materialization_info.run_id)

                value = dagster_run is not None and dagster_run.status == DagsterRunStatus.FAILURE

        return SerializableEntitySubset(key=asset_key, value=value)

    ####################
    # ASSET RECORDS / STORAGE IDS
    ####################

    def get_asset_record(self, asset_key: AssetKey) -> Optional["AssetRecord"]:
        from dagster._core.storage.event_log.base import AssetRecord

        return AssetRecord.blocking_get(self._loading_context, asset_key)

    def _event_type_for_key(self, asset_key: AssetKey) -> DagsterEventType:
        if self.asset_graph.get(asset_key).is_observable:
            return DagsterEventType.ASSET_OBSERVATION
        else:
            return DagsterEventType.ASSET_MATERIALIZATION

    @cached_method
    def _get_latest_materialization_or_observation_record(
        self, *, asset_partition: AssetKeyPartitionKey, before_cursor: Optional[int] = None
    ) -> Optional["EventLogRecord"]:
        """Returns the latest event log record for the given asset partition of an asset. For
        observable source assets, this will be an AssetObservation, otherwise it will be an
        AssetMaterialization.
        """
        # in the simple case, just use the asset record
        if (
            before_cursor is None
            and asset_partition.partition_key is None
            and not (
                self.asset_graph.has(asset_partition.asset_key)
                and self.asset_graph.get(asset_partition.asset_key).is_observable
            )
        ):
            asset_record = self.get_asset_record(asset_partition.asset_key)
            if asset_record is None:
                return None
            return asset_record.asset_entry.last_materialization_record

        records_filter = AssetRecordsFilter(
            asset_key=asset_partition.asset_key,
            asset_partitions=(
                [asset_partition.partition_key] if asset_partition.partition_key else None
            ),
            before_storage_id=before_cursor,
        )

        # For observable assets, we fetch the most recent observation and materialization and return
        # whichever is more recent. For non-observable assets, we just fetch the most recent
        # materialization.
        materialization_records = self.instance.fetch_materializations(
            records_filter, ascending=False, limit=1
        ).records
        if self.asset_graph.get(asset_partition.asset_key).is_observable:
            observation_records = self.instance.fetch_observations(
                records_filter, ascending=False, limit=1
            ).records
            all_records = sorted(
                [*materialization_records, *observation_records],
                key=lambda x: x.timestamp,
                reverse=True,
            )
        else:
            all_records = materialization_records
        return next(iter(all_records), None)

    @cached_method
    def _get_latest_materialization_or_observation_storage_ids_by_asset_partition(
        self, *, asset_key: AssetKey
    ) -> Mapping[AssetKeyPartitionKey, Optional[int]]:
        """Returns a mapping from asset partition to the latest storage id for that asset partition
        for all asset partitions associated with the given asset key.

        Note that for partitioned assets, an asset partition with a None partition key will be
        present in the mapping, representing the latest storage id for the asset as a whole.
        """
        asset_partition = AssetKeyPartitionKey(asset_key)
        latest_record = self._get_latest_materialization_or_observation_record(
            asset_partition=asset_partition
        )
        latest_storage_ids = {
            asset_partition: latest_record.storage_id if latest_record is not None else None
        }
        if self.asset_graph.get(asset_key).is_partitioned:
            latest_storage_ids.update(
                {
                    AssetKeyPartitionKey(asset_key, partition_key): storage_id
                    for partition_key, storage_id in self.instance.get_latest_storage_id_by_partition(
                        asset_key, event_type=self._event_type_for_key(asset_key)
                    ).items()
                }
            )
        return latest_storage_ids

    def get_latest_materialization_or_observation_storage_id(
        self, asset_partition: AssetKeyPartitionKey
    ) -> Optional[int]:
        """Returns the latest storage id for the given asset partition. If the asset has never been
        materialized, returns None.

        Args:
            asset_partition (AssetKeyPartitionKey): The asset partition to query.
        """
        if asset_partition.partition_key is None:
            record = self._get_latest_materialization_or_observation_record(
                asset_partition=asset_partition
            )
            return record.storage_id if record else None
        return self._get_latest_materialization_or_observation_storage_ids_by_asset_partition(
            asset_key=asset_partition.asset_key
        ).get(asset_partition)

    def asset_partition_has_materialization_or_observation(
        self,
        asset_partition: AssetKeyPartitionKey,
        after_cursor: Optional[int] = None,
    ) -> bool:
        """Returns True if there is a materialization record for the given asset partition after
        the specified cursor.

        Args:
            asset_partition (AssetKeyPartitionKey): The asset partition to query.
            after_cursor (Optional[int]): Filter parameter such that only records with a storage_id
                greater than this value will be considered.
        """
        asset_key = asset_partition.asset_key
        if self.asset_graph.has(asset_key) and self.asset_graph.get(asset_key).is_materializable:
            asset_record = self.get_asset_record(asset_key)
            if (
                asset_record is None
                or asset_record.asset_entry.last_materialization_record is None
                or (
                    after_cursor
                    and asset_record.asset_entry.last_materialization_record.storage_id
                    <= after_cursor
                )
            ):
                return False
        return (self.get_latest_materialization_or_observation_storage_id(asset_partition) or 0) > (
            after_cursor or 0
        )

    def get_latest_materialization_or_observation_record(
        self,
        asset_partition: AssetKeyPartitionKey,
        after_cursor: Optional[int] = None,
        before_cursor: Optional[int] = None,
    ) -> Optional["EventLogRecord"]:
        """Returns the latest record for the given asset partition given the specified cursors.

        Args:
            asset_partition (AssetKeyPartitionKey): The asset partition to query.
            after_cursor (Optional[int]): Filter parameter such that only records with a storage_id
                greater than this value will be considered.
            before_cursor (Optional[int]): Filter parameter such that only records with a storage_id
                less than this value will be considered.
        """
        check.param_invariant(
            not (after_cursor and before_cursor),
            "before_cursor",
            "Cannot set both before_cursor and after_cursor",
        )

        # first, do a quick check to eliminate the case where we know there is no record
        if not self.asset_partition_has_materialization_or_observation(
            asset_partition, after_cursor
        ):
            return None
        # then, if the before_cursor is after our latest record's storage id, we can just return
        # the latest record
        elif (before_cursor or 0) > (
            self.get_latest_materialization_or_observation_storage_id(asset_partition) or 0
        ):
            return self._get_latest_materialization_or_observation_record(
                asset_partition=asset_partition
            )
        # otherwise, do the explicit query
        return self._get_latest_materialization_or_observation_record(
            asset_partition=asset_partition, before_cursor=before_cursor
        )

    ####################
    # OBSERVATIONS
    ####################

    @cached_method
    def next_version_record(
        self,
        *,
        asset_key: AssetKey,
        after_cursor: Optional[int],
        data_version: Optional[DataVersion],
    ) -> Optional["EventLogRecord"]:
        has_more = True
        cursor = None
        while has_more:
            result = self.instance.fetch_observations(
                AssetRecordsFilter(asset_key=asset_key, after_storage_id=after_cursor),
                limit=RECORD_BATCH_SIZE,
                cursor=cursor,
                ascending=True,
            )
            has_more = result.has_more
            cursor = result.cursor
            for record in result.records:
                record_version = extract_data_version_from_entry(record.event_log_entry)
                if record_version is not None and record_version != data_version:
                    return record

        # no records found with a new data version
        return None

    ####################
    # RUNS
    ####################

    @cached_method
    def _get_run_record_by_id(self, *, run_id: str) -> Optional[RunRecord]:
        return self.instance.get_run_record_by_id(run_id)

    def _get_run_by_id(self, run_id: str) -> Optional[DagsterRun]:
        run_record = self._get_run_record_by_id(run_id=run_id)
        if run_record is not None:
            return run_record.dagster_run
        return None

    def run_has_tag(self, run_id: str, tag_key: str, tag_value: Optional[str]) -> bool:
        run = self._get_run_by_id(run_id)
        if run is None:
            return False

        run_tags = run.tags

        if tag_value is None:
            return tag_key in run_tags
        else:
            return run_tags.get(tag_key) == tag_value

    @cached_method
    def _get_planned_materializations_for_run_from_snapshot(
        self, *, snapshot_id: str
    ) -> AbstractSet[AssetKey]:
        execution_plan_snapshot = check.not_none(
            self._instance.get_execution_plan_snapshot(snapshot_id)
        )
        return execution_plan_snapshot.asset_selection

    @cached_method
    def _get_planned_materializations_for_run_from_events(
        self, *, run_id: str
    ) -> AbstractSet[AssetKey]:
        """Provides a fallback for fetching the planned materializations for a run from
        the ASSET_MATERIALIZATION_PLANNED events in the event log, in cases where this information
        is not available on the DagsterRun object.

        Args:
            run_id (str): The run id
        """
        materializations_planned = self.instance.get_records_for_run(
            run_id=run_id, of_type=DagsterEventType.ASSET_MATERIALIZATION_PLANNED
        ).records
        return set(cast(AssetKey, record.asset_key) for record in materializations_planned)

    def get_planned_materializations_for_run(self, run_id: str) -> AbstractSet[AssetKey]:
        """Returns the set of asset keys that are planned to be materialized by the run.

        Args:
            run_id (str): The run id
        """
        run = self._get_run_by_id(run_id=run_id)
        if run is None:
            return set()
        elif run.asset_selection:
            return run.asset_selection
        elif run.execution_plan_snapshot_id:
            return self._get_planned_materializations_for_run_from_snapshot(
                snapshot_id=check.not_none(run.execution_plan_snapshot_id)
            )
        else:
            # must resort to querying the event log
            return self._get_planned_materializations_for_run_from_events(run_id=run_id)

    def is_asset_planned_for_run(
        self, run_id: str, asset: Union[AssetKey, AssetKeyPartitionKey]
    ) -> bool:
        """Returns True if the asset is planned to be materialized by the run."""
        run = self._get_run_by_id(run_id=run_id)
        if not run:
            return False

        if isinstance(asset, AssetKeyPartitionKey):
            asset_key = asset.asset_key
            if run.tags.get(PARTITION_NAME_TAG) != asset.partition_key:
                return False
        else:
            asset_key = asset

        return asset_key in self.get_planned_materializations_for_run(run_id=run_id)

    @cached_method
    def get_current_materializations_for_run(self, *, run_id: str) -> AbstractSet[AssetKey]:
        """Returns the set of asset keys that have been materialized by a given run.

        Args:
            run_id (str): The run id
        """
        materializations = self.instance.get_records_for_run(
            run_id=run_id,
            of_type=DagsterEventType.ASSET_MATERIALIZATION,
        ).records
        return set(cast(AssetKey, record.asset_key) for record in materializations)

    ####################
    # BACKFILLS
    ####################

    @cached_method
    def get_active_backfill_datas(self) -> Sequence["AssetBackfillData"]:
        from dagster._core.execution.backfill import BulkActionsFilter, BulkActionStatus

        active_backfills = [
            backfill
            for backfill in self.instance.get_backfills(
                filters=BulkActionsFilter(statuses=[BulkActionStatus.REQUESTED])
            )
            if backfill.is_asset_backfill
        ]

        backfill_datas = []
        for backfill in active_backfills:
            try:
                backfill_datas.append(backfill.get_asset_backfill_data(self.asset_graph))
            except DagsterDefinitionChangedDeserializationError:
                self._logger.warning(
                    f"Not considering assets in backfill {backfill.backfill_id} since its"
                    " data could not be deserialized"
                )
                # Backfill can't be loaded, so no risk of the assets interfering
                continue
        return backfill_datas

    @cached_method
    def get_active_backfill_target_asset_graph_subset(self) -> AssetGraphSubset:
        """Returns an AssetGraphSubset representing the set of assets that are currently targeted by
        an active asset backfill.
        """
        result = AssetGraphSubset()
        for data in self.get_active_backfill_datas():
            result |= data.target_subset

        return result

    @cached_method
    def get_active_backfill_in_progress_asset_graph_subset(self) -> AssetGraphSubset:
        """Returns an AssetGraphSubset representing the set of assets that are currently targeted by
        an active asset backfill and have not yet been materialized or failed.
        """
        result = AssetGraphSubset()
        for data in self.get_active_backfill_datas():
            in_progress_subset = (
                data.target_subset - data.materialized_subset - data.failed_and_downstream_subset
            )
            result |= in_progress_subset

        return result

    ####################
    # PARTITIONS
    ####################

    def get_materialized_partitions(
        self, asset_key: AssetKey, before_cursor: Optional[int] = None
    ) -> set[str]:
        """Returns a list of the partitions that have been materialized for the given asset key.

        Args:
            asset_key (AssetKey): The asset key.
            before_cursor (Optional[int]): The cursor before which to look for materialized
                partitions. If not provided, will look at all materializations.
        """
        if (
            before_cursor not in self._asset_partitions_cache
            or asset_key not in self._asset_partitions_cache[before_cursor]
        ):
            self._asset_partitions_cache[before_cursor][asset_key] = (
                self.instance.get_materialized_partitions(
                    asset_key=asset_key, before_cursor=before_cursor
                )
            )

        return self._asset_partitions_cache[before_cursor][asset_key]

    ####################
    # DYNAMIC PARTITIONS
    ####################

    def get_dynamic_partitions(self, partitions_def_name: str) -> Sequence[str]:
        """Returns a list of partitions for a partitions definition."""
        if partitions_def_name not in self._dynamic_partitions_cache:
            self._dynamic_partitions_cache[partitions_def_name] = (
                self.instance.get_dynamic_partitions(partitions_def_name)
            )
        return self._dynamic_partitions_cache[partitions_def_name]

    def has_dynamic_partition(self, partitions_def_name: str, partition_key: str) -> bool:
        return partition_key in self.get_dynamic_partitions(partitions_def_name)

    @cached_method
    def asset_partitions_with_newly_updated_parents_and_new_cursor(
        self,
        *,
        latest_storage_id: Optional[int],
        child_asset_key: AssetKey,
        map_old_time_partitions: bool = True,
        max_child_partitions: Optional[int] = None,
    ) -> tuple[AbstractSet[AssetKeyPartitionKey], Optional[int]]:
        """Finds asset partitions of the given child whose parents have been materialized since
        latest_storage_id.
        """
        max_storage_ids = [
            self.get_latest_materialization_or_observation_storage_id(
                AssetKeyPartitionKey(child_asset_key)
            )
        ]
        child_asset = self.asset_graph.get(child_asset_key)
        if not child_asset.parent_keys:
            return set(), max(filter(None, [latest_storage_id, *max_storage_ids]), default=None)

        child_time_partitions_def = get_time_partitions_def(child_asset.partitions_def)
        child_asset_partitions_with_updated_parents = set()
        for parent_asset_key in self.asset_graph.get(child_asset_key).parent_keys:
            # ignore non-existent parents
            if not self.asset_graph.has(parent_asset_key):
                continue

            # if the parent has not been updated at all since the latest_storage_id, then skip
            if not self.get_asset_partitions_updated_after_cursor(
                asset_key=parent_asset_key,
                asset_partitions=None,
                after_cursor=latest_storage_id,
                respect_materialization_data_versions=False,
            ):
                continue

            # keep track of the maximum storage id that we've seen for a given parent
            max_storage_ids.append(
                self.get_latest_materialization_or_observation_storage_id(
                    AssetKeyPartitionKey(parent_asset_key)
                )
            )

            parent_partitions_def: PartitionsDefinition = self.asset_graph.get(
                parent_asset_key
            ).partitions_def
            if parent_partitions_def is None:
                latest_parent_record = check.not_none(
                    self.get_latest_materialization_or_observation_record(
                        AssetKeyPartitionKey(parent_asset_key), after_cursor=latest_storage_id
                    )
                )
                for child_partition_key in (
                    self.asset_graph.get_child_partition_keys_of_parent(
                        dynamic_partitions_store=self,
                        parent_partition_key=None,
                        parent_asset_key=parent_asset_key,
                        child_asset_key=child_asset_key,
                        current_time=self.evaluation_time,
                    )
                    if child_asset.partitions_def
                    else [None]
                ):
                    if not (
                        # when mapping from unpartitioned assets to time partitioned assets, we ignore
                        # historical time partitions
                        not map_old_time_partitions
                        and child_time_partitions_def is not None
                        and get_time_partition_key(child_asset.partitions_def, child_partition_key)
                        != child_time_partitions_def.get_last_partition_key(
                            current_time=self.evaluation_time
                        )
                    ) and not self.is_asset_planned_for_run(
                        latest_parent_record.run_id, child_asset_key
                    ):
                        child_asset_partitions_with_updated_parents.add(
                            AssetKeyPartitionKey(child_asset_key, child_partition_key)
                        )
            else:
                # we know a parent updated, and because the parent has a partitions def and the
                # child does not, the child could not have been materialized in the same run
                if child_asset.partitions_def is None:
                    child_asset_partitions_with_updated_parents = {
                        AssetKeyPartitionKey(child_asset_key)
                    }
                    break

                # the set of asset partitions which have been updated since the latest storage id
                parent_partitions_subset = self.get_asset_subset_updated_after_cursor(
                    asset_key=parent_asset_key,
                    after_cursor=latest_storage_id,
                    require_data_version_update=False,
                ).subset_value

                # we are mapping from the partitions of the parent asset to the partitions of
                # the child asset
                partition_mapping = self.asset_graph.get_partition_mapping(
                    key=child_asset_key, parent_asset_key=parent_asset_key
                )
                try:
                    child_partitions_subset = (
                        partition_mapping.get_downstream_partitions_for_partitions(
                            parent_partitions_subset,
                            upstream_partitions_def=parent_partitions_def,
                            downstream_partitions_def=child_asset.partitions_def,
                            dynamic_partitions_store=self,
                            current_time=self.evaluation_time,
                        )
                    )
                except DagsterInvalidDefinitionError as e:
                    # add a more helpful error message to the stack
                    raise DagsterInvalidDefinitionError(
                        f"Could not map partitions between parent {parent_asset_key.to_string()} "
                        f"and child {child_asset_key.to_string()}."
                    ) from e

                # Prefer more recent time-based partitions, particularly if we end up filtering
                # using max_child_partitions (not a strict guarantee that this will always return
                # the most recent partitions in time though)
                child_partitions = sorted(
                    child_partitions_subset.get_partition_keys(), reverse=True
                )

                if max_child_partitions is not None:
                    child_partitions = child_partitions[:max_child_partitions]

                for child_partition in child_partitions:
                    # we need to see if the child is planned for the same run, but this is
                    # expensive, so we try to avoid doing so in as many situations as possible
                    child_asset_partition = AssetKeyPartitionKey(child_asset_key, child_partition)
                    if (
                        # if child has a different partitions def than the parent, then it must
                        # have been executed in a different run, so it's a valid candidate
                        child_asset.partitions_def != parent_partitions_def
                        # if child partition key is not the same as any newly materialized
                        # parent key, then it could not have been executed in the same run as
                        # its parent
                        or child_partition not in parent_partitions_subset
                        # if child partition is not failed or in progress, then if it was
                        # executed in the same run as its parent, then it must have been
                        # materialized more recently than its parent
                        or child_partition
                        not in self.get_failed_or_in_progress_subset(asset_key=child_asset_key)
                    ):
                        child_asset_partitions_with_updated_parents.add(child_asset_partition)
                    else:
                        # manually query to see if this asset partition was intended to be
                        # executed in the same run as its parent
                        latest_partition_record = check.not_none(
                            self.get_latest_materialization_or_observation_record(
                                AssetKeyPartitionKey(parent_asset_key, child_partition),
                                after_cursor=latest_storage_id,
                            )
                        )
                        if not self.is_asset_planned_for_run(
                            latest_partition_record.run_id, child_asset_key
                        ):
                            child_asset_partitions_with_updated_parents.add(child_asset_partition)

        # the new latest storage id will be the greatest observed storage id among this asset and
        # its parents
        new_latest_storage_id = max(
            filter(None, [latest_storage_id, *max_storage_ids]), default=None
        )
        return (child_asset_partitions_with_updated_parents, new_latest_storage_id)

    ####################
    # RECONCILIATION
    ####################

    def _asset_partition_versions_updated_after_cursor(
        self,
        asset_key: AssetKey,
        asset_partitions: AbstractSet[AssetKeyPartitionKey],
        after_cursor: int,
    ) -> AbstractSet[AssetKeyPartitionKey]:
        # we already know asset partitions are updated after the cursor if they've been updated
        # after a cursor that's greater than or equal to this one
        updated_asset_partitions = {
            ap
            for ap in asset_partitions
            if ap in self._asset_partition_versions_updated_after_cursor_cache
            and self._asset_partition_versions_updated_after_cursor_cache[ap] <= after_cursor
        }
        to_query_asset_partitions = asset_partitions - updated_asset_partitions
        if not to_query_asset_partitions:
            return updated_asset_partitions

        if not self.asset_graph.get(asset_key).is_partitioned:
            asset_partition = AssetKeyPartitionKey(asset_key)
            latest_record = self.get_latest_materialization_or_observation_record(
                asset_partition, after_cursor=after_cursor
            )
            latest_data_version = (
                extract_data_version_from_entry(latest_record.event_log_entry)
                if latest_record
                else None
            )
            previous_record = self.get_latest_materialization_or_observation_record(
                asset_partition, before_cursor=after_cursor + 1
            )
            previous_data_version = (
                extract_data_version_from_entry(previous_record.event_log_entry)
                if previous_record
                else None
            )
            return set([asset_partition]) if latest_data_version != previous_data_version else set()

        partition_keys = [
            asset_partition.partition_key
            for asset_partition in asset_partitions
            if asset_partition.partition_key
        ]
        updated_partition_keys = (
            self.instance.event_log_storage.get_updated_data_version_partitions(
                asset_key=asset_key,
                partitions=partition_keys,
                since_storage_id=after_cursor,
            )
        )
        return set(
            AssetKeyPartitionKey(asset_key, partition_key)
            for partition_key in updated_partition_keys
        )

    def get_asset_partitions_updated_after_cursor(
        self,
        asset_key: AssetKey,
        asset_partitions: Optional[AbstractSet[AssetKeyPartitionKey]],
        after_cursor: Optional[int],
        respect_materialization_data_versions: bool,
    ) -> AbstractSet[AssetKeyPartitionKey]:
        """Returns the set of asset partitions that have been updated after the given cursor.

        Args:
            asset_key (AssetKey): The asset key to check.
            asset_partitions (Optional[Sequence[AssetKeyPartitionKey]]): If supplied, will filter
                the set of checked partitions to the given partitions.
            after_cursor (Optional[int]): The cursor after which to look for updates.
            respect_materialization_data_versions (bool): If True, will use data versions to filter
                out asset partitions which were materialized, but not have not had their data
                versions changed since the given cursor.
                NOTE: This boolean has been temporarily disabled
        """
        if not self.asset_partition_has_materialization_or_observation(
            AssetKeyPartitionKey(asset_key), after_cursor=after_cursor
        ):
            return set()

        last_storage_id_by_asset_partition = (
            self._get_latest_materialization_or_observation_storage_ids_by_asset_partition(
                asset_key=asset_key
            )
        )

        if asset_partitions is None:
            updated_after_cursor = {
                asset_partition
                for asset_partition, latest_storage_id in last_storage_id_by_asset_partition.items()
                if (latest_storage_id or 0) > (after_cursor or 0)
            }
        else:
            # Optimized for the case where there are many partitions and last_storage_id_by_asset_partition
            # is large, but we're only looking for the result for a small number of partitions
            updated_after_cursor = set()
            for asset_partition in asset_partitions:
                latest_storage_id = last_storage_id_by_asset_partition.get(asset_partition)
                if latest_storage_id is not None and latest_storage_id > (after_cursor or 0):
                    updated_after_cursor.add(asset_partition)

        if not updated_after_cursor:
            return set()
        if after_cursor is None or (
            not self.asset_graph.get(asset_key).is_observable
            and not respect_materialization_data_versions
        ):
            return updated_after_cursor

        return self._asset_partition_versions_updated_after_cursor(
            asset_key, updated_after_cursor, after_cursor
        )

    @cached_method
    def get_asset_subset_updated_after_cursor(
        self, *, asset_key: AssetKey, after_cursor: Optional[int], require_data_version_update: bool
    ) -> SerializableEntitySubset[AssetKey]:
        """Returns the AssetSubset of the given asset that has been updated after the given cursor."""
        partitions_def = self.asset_graph.get(asset_key).partitions_def
        updated_asset_partitions = self.get_asset_partitions_updated_after_cursor(
            asset_key,
            asset_partitions=None,
            after_cursor=after_cursor,
            respect_materialization_data_versions=require_data_version_update,
        )
        if partitions_def is None:
            validated_asset_partitions = {
                ap for ap in updated_asset_partitions if ap.partition_key is None
            }
        else:
            validated_asset_partitions = {
                ap
                for ap in updated_asset_partitions
                if ap.partition_key is not None
                and partitions_def.has_partition_key(
                    partition_key=ap.partition_key,
                    dynamic_partitions_store=self,
                    current_time=self.evaluation_time,
                )
            }

        # TODO: replace this return value with EntitySubset
        return ValidAssetSubset.from_asset_partitions_set(
            asset_key, partitions_def, validated_asset_partitions
        )

    @cached_method
    def get_asset_subset_updated_after_time(
        self, *, asset_key: AssetKey, after_time: datetime
    ) -> SerializableEntitySubset[AssetKey]:
        """Returns the AssetSubset of the given asset that has been updated after the given time."""
        partitions_def = self.asset_graph.get(asset_key).partitions_def

        method = (
            self.instance.fetch_materializations
            if self._event_type_for_key(asset_key) == DagsterEventType.ASSET_MATERIALIZATION
            else self.instance.fetch_observations
        )
        first_event_after_time = next(
            iter(
                method(
                    AssetRecordsFilter(asset_key=asset_key, after_timestamp=after_time.timestamp()),
                    limit=1,
                    ascending=True,
                ).records
            ),
            None,
        )
        if not first_event_after_time:
            # TODO: replace this return value with EntitySubset
            return ValidAssetSubset.empty(asset_key, partitions_def=partitions_def)
        else:
            return self.get_asset_subset_updated_after_cursor(
                asset_key=asset_key,
                after_cursor=first_event_after_time.storage_id - 1,
                require_data_version_update=False,
            )

    def get_parent_asset_partitions_updated_after_child(
        self,
        *,
        asset_partition: AssetKeyPartitionKey,
        parent_asset_partitions: AbstractSet[AssetKeyPartitionKey],
        respect_materialization_data_versions: bool,
        ignored_parent_keys: AbstractSet[AssetKey],
    ) -> AbstractSet[AssetKeyPartitionKey]:
        """Returns values inside parent_asset_partitions that correspond to asset partitions that
        have been updated since the latest materialization of asset_partition.
        """
        parent_asset_partitions_by_key: dict[AssetKey, set[AssetKeyPartitionKey]] = defaultdict(set)
        for parent in parent_asset_partitions:
            parent_asset_partitions_by_key[parent.asset_key].add(parent)

        partitions_def = self.asset_graph.get(asset_partition.asset_key).partitions_def
        updated_parents = set()

        for parent_key, parent_asset_partitions in parent_asset_partitions_by_key.items():
            # ignore updates to particular parents
            if parent_key in ignored_parent_keys:
                continue

            # ignore non-existent parents
            if not self.asset_graph.has(parent_key):
                continue

            # when mapping from unpartitioned assets to time partitioned assets, we ignore
            # historical time partitions
            if (
                isinstance(partitions_def, TimeWindowPartitionsDefinition)
                and not self.asset_graph.get(parent_key).is_partitioned
                and asset_partition.partition_key
                != partitions_def.get_last_partition_key(
                    current_time=self.evaluation_time, dynamic_partitions_store=self
                )
            ):
                continue

            updated_parents.update(
                self.get_asset_partitions_updated_after_cursor(
                    asset_key=parent_key,
                    asset_partitions=parent_asset_partitions,
                    after_cursor=self.get_latest_materialization_or_observation_storage_id(
                        asset_partition
                    ),
                    respect_materialization_data_versions=respect_materialization_data_versions,
                )
            )
        return updated_parents

    def have_ignorable_partition_mapping_for_outdated(
        self, asset_key: AssetKey, upstream_asset_key: AssetKey
    ) -> bool:
        """Returns whether the given assets have a partition mapping between them which can be
        ignored in the context of calculating if an asset is outdated or not.

        These mappings are ignored in cases where respecting them would require an unrealistic
        number of upstream partitions to be in a 'good' state before allowing a downstream asset
        to be considered up to date.
        """
        # Self partition mappings impose constraints on all historical partitions
        return asset_key == upstream_asset_key

    @cached_method
    def get_outdated_ancestors(
        self, *, asset_partition: AssetKeyPartitionKey
    ) -> AbstractSet[AssetKey]:
        asset_key = asset_partition.asset_key
        partition_key = asset_partition.partition_key
        if not (
            self.asset_graph.has(asset_key) and self.asset_graph.get(asset_key).is_materializable
        ):
            return set()

        parent_asset_partitions = self.asset_graph.get_parents_partitions(
            dynamic_partitions_store=self,
            current_time=self._evaluation_time,
            asset_key=asset_key,
            partition_key=partition_key,
        ).parent_partitions

        # the set of parent keys which we don't need to check
        ignored_parent_keys = {
            parent
            for parent in self.asset_graph.get(asset_key).parent_keys
            if self.have_ignorable_partition_mapping_for_outdated(asset_key, parent)
        }

        updated_parents = self.get_parent_asset_partitions_updated_after_child(
            asset_partition=asset_partition,
            parent_asset_partitions=parent_asset_partitions,
            respect_materialization_data_versions=self._respect_materialization_data_versions,
            ignored_parent_keys=ignored_parent_keys,
        )

        root_unreconciled_ancestors = {asset_key} if updated_parents else set()

        # recurse over parents
        for parent in set(parent_asset_partitions) - updated_parents:
            if parent.asset_key in ignored_parent_keys:
                continue
            root_unreconciled_ancestors.update(self.get_outdated_ancestors(asset_partition=parent))

        return root_unreconciled_ancestors
