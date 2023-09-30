import logging
from collections import defaultdict, deque
from datetime import datetime
from typing import (
    TYPE_CHECKING,
    AbstractSet,
    Callable,
    Dict,
    FrozenSet,
    Iterable,
    Mapping,
    Optional,
    Sequence,
    Set,
    Tuple,
    Union,
    cast,
)

import pendulum

import dagster._check as check
from dagster._core.definitions.asset_graph import AssetGraph, ToposortedPriorityQueue
from dagster._core.definitions.asset_graph_subset import AssetGraphSubset
from dagster._core.definitions.data_version import (
    DATA_VERSION_TAG,
    DataVersion,
    extract_data_version_from_entry,
)
from dagster._core.definitions.events import AssetKey, AssetKeyPartitionKey
from dagster._core.definitions.partition import DynamicPartitionsDefinition, PartitionsSubset
from dagster._core.definitions.time_window_partitions import (
    TimeWindowPartitionsDefinition,
    get_time_partition_key,
    get_time_partitions_def,
)
from dagster._core.errors import DagsterDefinitionChangedDeserializationError
from dagster._core.events import DagsterEventType
from dagster._core.instance import DagsterInstance, DynamicPartitionsStore
from dagster._core.storage.dagster_run import (
    DagsterRun,
    RunRecord,
)
from dagster._core.storage.tags import PARTITION_NAME_TAG
from dagster._utils.cached_method import cached_method

if TYPE_CHECKING:
    from dagster._core.storage.event_log import EventLogRecord
    from dagster._core.storage.event_log.base import AssetRecord


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
        asset_graph: AssetGraph,
        evaluation_time: Optional[datetime] = None,
        logger: Optional[logging.Logger] = None,
    ):
        self._instance = instance
        self._asset_graph = asset_graph
        self._logger = logger or logging.getLogger("dagster")

        self._asset_record_cache: Dict[AssetKey, Optional[AssetRecord]] = {}
        self._asset_partitions_cache: Dict[Optional[int], Dict[AssetKey, Set[str]]] = defaultdict(
            dict
        )
        self._asset_partition_versions_updated_after_cursor_cache: Dict[
            AssetKeyPartitionKey, int
        ] = {}

        self._dynamic_partitions_cache: Dict[str, Sequence[str]] = {}

        self._evaluation_time = evaluation_time if evaluation_time else pendulum.now("UTC")

        self._outdated_ancestors_cache: Dict[AssetKeyPartitionKey, Set[AssetKey]] = {}
        self._respect_materialization_data_versions = (
            self._instance.auto_materialize_respect_materialization_data_versions
        )

    @property
    def instance(self) -> DagsterInstance:
        return self._instance

    @property
    def asset_graph(self) -> AssetGraph:
        return self._asset_graph

    @property
    def evaluation_time(self) -> datetime:
        return self._evaluation_time

    ####################
    # QUERY BATCHING
    ####################

    def prefetch_asset_records(self, asset_keys: Iterable[AssetKey]):
        """For performance, batches together queries for selected assets."""
        keys_to_fetch = set(asset_keys) - set(self._asset_record_cache.keys())
        if len(keys_to_fetch) == 0:
            return
        # get all asset records for selected assets that aren't already cached
        asset_records = self.instance.get_asset_records(list(keys_to_fetch))
        for asset_record in asset_records:
            self._asset_record_cache[asset_record.asset_entry.asset_key] = asset_record
        for key in asset_keys:
            if key not in self._asset_record_cache:
                self._asset_record_cache[key] = None

    ####################
    # ASSET STATUS CACHE
    ####################

    @cached_method
    def get_failed_or_in_progress_subset(self, *, asset_key: AssetKey) -> PartitionsSubset:
        """Returns a PartitionsSubset representing the set of partitions that are either in progress
        or whose last materialization attempt failed.
        """
        from dagster._core.storage.partition_status_cache import (
            get_and_update_asset_status_cache_value,
        )

        partitions_def = check.not_none(self.asset_graph.get_partitions_def(asset_key))
        asset_record = self.get_asset_record(asset_key)
        cache_value = get_and_update_asset_status_cache_value(
            instance=self.instance,
            asset_key=asset_key,
            partitions_def=partitions_def,
            dynamic_partitions_loader=self,
            asset_record=asset_record,
        )
        if cache_value is None:
            return partitions_def.empty_subset()

        return cache_value.deserialize_failed_partition_subsets(
            partitions_def
        ) | cache_value.deserialize_in_progress_partition_subsets(partitions_def)

    ####################
    # ASSET RECORDS / STORAGE IDS
    ####################

    def has_cached_asset_record(self, asset_key: AssetKey) -> bool:
        return asset_key in self._asset_record_cache

    def get_asset_record(self, asset_key: AssetKey) -> Optional["AssetRecord"]:
        if asset_key not in self._asset_record_cache:
            self._asset_record_cache[asset_key] = next(
                iter(self.instance.get_asset_records([asset_key])), None
            )
        return self._asset_record_cache[asset_key]

    def _event_type_for_key(self, asset_key: AssetKey) -> DagsterEventType:
        if self.asset_graph.is_source(asset_key):
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
        from dagster._core.event_api import EventRecordsFilter

        # in the simple case, just use the asset record
        if (
            before_cursor is None
            and asset_partition.partition_key is None
            and not self.asset_graph.is_observable(asset_partition.asset_key)
        ):
            asset_record = self.get_asset_record(asset_partition.asset_key)
            if asset_record is None:
                return None
            return asset_record.asset_entry.last_materialization_record

        records = self.instance.get_event_records(
            EventRecordsFilter(
                event_type=self._event_type_for_key(asset_partition.asset_key),
                asset_key=asset_partition.asset_key,
                asset_partitions=(
                    [asset_partition.partition_key] if asset_partition.partition_key else None
                ),
                before_cursor=before_cursor,
            ),
            ascending=False,
            limit=1,
        )
        return next(iter(records), None)

    @cached_method
    def get_latest_storage_id_for_event_type(
        self, *, event_type: DagsterEventType
    ) -> Optional[int]:
        """Returns the latest storage id across all events of the given event_type.

        Args:
            event_type (DagsterEventType): The event type to query for.
        """
        from dagster._core.event_api import EventRecordsFilter

        latest_record = next(
            iter(
                self.instance.get_event_records(
                    event_records_filter=EventRecordsFilter(event_type=event_type),
                    limit=1,
                )
            ),
            None,
        )
        if latest_record is not None:
            return latest_record.storage_id
        return None

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
        if self.asset_graph.is_partitioned(asset_key):
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
        if not self.asset_graph.is_source(asset_partition.asset_key):
            asset_record = self.get_asset_record(asset_partition.asset_key)
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
        from dagster._core.event_api import EventRecordsFilter

        for record in self.instance.get_event_records(
            EventRecordsFilter(
                event_type=DagsterEventType.ASSET_OBSERVATION,
                asset_key=asset_key,
                after_cursor=after_cursor,
            ),
            ascending=True,
        ):
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

    def run_has_tag(self, run_id: str, tag_key: str, tag_value: str) -> bool:
        return cast(DagsterRun, self._get_run_by_id(run_id)).tags.get(tag_key) == tag_value

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
    def get_active_backfill_target_asset_graph_subset(self) -> AssetGraphSubset:
        """Returns an AssetGraphSubset representing the set of assets that are currently targeted by
        an active asset backfill.
        """
        from dagster._core.execution.asset_backfill import AssetBackfillData
        from dagster._core.execution.backfill import BulkActionStatus

        asset_backfills = [
            backfill
            for backfill in self.instance.get_backfills(status=BulkActionStatus.REQUESTED)
            if backfill.is_asset_backfill
        ]

        result = AssetGraphSubset(self.asset_graph)
        for asset_backfill in asset_backfills:
            if asset_backfill.serialized_asset_backfill_data is None:
                check.failed("Asset backfill missing serialized_asset_backfill_data")

            try:
                asset_backfill_data = AssetBackfillData.from_serialized(
                    asset_backfill.serialized_asset_backfill_data,
                    self.asset_graph,
                    asset_backfill.backfill_timestamp,
                )
            except DagsterDefinitionChangedDeserializationError:
                self._logger.warning(
                    f"Not considering assets in backfill {asset_backfill.backfill_id} since its"
                    " data could not be deserialized"
                )
                # Backfill can't be loaded, so no risk of the assets interfering
                continue

            result |= asset_backfill_data.target_subset

        return result

    ####################
    # PARTITIONS
    ####################

    def get_materialized_partitions(
        self, asset_key: AssetKey, before_cursor: Optional[int] = None
    ) -> Set[str]:
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

    def asset_partitions_with_newly_updated_parents_and_new_latest_storage_id(
        self,
        latest_storage_id: Optional[int],
        target_asset_keys: FrozenSet[AssetKey],
        target_asset_keys_and_parents: FrozenSet[AssetKey],
        can_reconcile_fn: Callable[[AssetKeyPartitionKey], bool] = lambda _: True,
        map_old_time_partitions: bool = True,
    ) -> Tuple[AbstractSet[AssetKeyPartitionKey], Optional[int]]:
        """Finds asset partitions in the given selection whose parents have been materialized since
        latest_storage_id.

        Returns:
            - A set of asset partitions.
            - The latest observed storage_id across all relevant assets. Can be used to avoid scanning
                the same events the next time this function is called.
        """
        result_asset_partitions: Set[AssetKeyPartitionKey] = set()
        result_latest_storage_id = latest_storage_id

        for asset_key in target_asset_keys_and_parents:
            if self.asset_graph.is_source(asset_key) and not self.asset_graph.is_observable(
                asset_key
            ):
                continue

            # the set of asset partitions which have been updated since the latest storage id
            new_asset_partitions = self.get_asset_partitions_updated_after_cursor(
                asset_key=asset_key,
                asset_partitions=None,
                after_cursor=latest_storage_id,
                # we don't need to use asset versions here because we will filter out any materialized
                # but not updated partitions in a later step
                respect_materialization_data_versions=False,
            )
            if not new_asset_partitions:
                continue

            partitions_def = self.asset_graph.get_partitions_def(asset_key)
            if partitions_def is None:
                latest_record = check.not_none(
                    self.get_latest_materialization_or_observation_record(
                        AssetKeyPartitionKey(asset_key)
                    )
                )
                for child in self.asset_graph.get_children_partitions(
                    dynamic_partitions_store=self,
                    current_time=self.evaluation_time,
                    asset_key=asset_key,
                ):
                    child_partitions_def = self.asset_graph.get_partitions_def(child.asset_key)
                    child_time_partitions_def = get_time_partitions_def(child_partitions_def)
                    if (
                        child.asset_key in target_asset_keys
                        and not (
                            # when mapping from unpartitioned assets to time partitioned assets, we ignore
                            # historical time partitions
                            not map_old_time_partitions
                            and child_time_partitions_def is not None
                            and get_time_partition_key(child_partitions_def, child.partition_key)
                            != child_time_partitions_def.get_last_partition_key(
                                current_time=self.evaluation_time
                            )
                        )
                        and not self.is_asset_planned_for_run(latest_record.run_id, child.asset_key)
                    ):
                        result_asset_partitions.add(child)
            else:
                partitions_subset = partitions_def.empty_subset().with_partition_keys(
                    [
                        asset_partition.partition_key
                        for asset_partition in new_asset_partitions
                        if asset_partition.partition_key is not None
                        and partitions_def.has_partition_key(
                            asset_partition.partition_key,
                            dynamic_partitions_store=self,
                            current_time=self.evaluation_time,
                        )
                    ]
                )
                for child in self.asset_graph.get_children(asset_key):
                    child_partitions_def = self.asset_graph.get_partitions_def(child)
                    if child not in target_asset_keys:
                        continue
                    elif not child_partitions_def:
                        result_asset_partitions.add(AssetKeyPartitionKey(child, None))
                    else:
                        # we are mapping from the partitions of the parent asset to the partitions of
                        # the child asset
                        partition_mapping = self.asset_graph.get_partition_mapping(child, asset_key)
                        child_partitions_subset = (
                            partition_mapping.get_downstream_partitions_for_partitions(
                                partitions_subset,
                                downstream_partitions_def=child_partitions_def,
                                dynamic_partitions_store=self,
                                current_time=self.evaluation_time,
                            )
                        )
                        for child_partition in child_partitions_subset.get_partition_keys():
                            # we need to see if the child is planned for the same run, but this is
                            # expensive, so we try to avoid doing so in as many situations as possible
                            child_asset_partition = AssetKeyPartitionKey(child, child_partition)
                            if not can_reconcile_fn(child_asset_partition):
                                continue
                            elif (
                                # if child has a different partitions def than the parent, then it must
                                # have been executed in a different run, so it's a valid candidate
                                child_partitions_def != partitions_def
                                # if child partition key is not the same as any newly materialized
                                # parent key, then it could not have been executed in the same run as
                                # its parent
                                or child_partition not in partitions_subset
                                # if child partition is not failed or in progress, then even if it was
                                # executed in the same run, we can filter it out later with an is_reconciled
                                # check (cheaper than the below logic)
                                or child_partition
                                not in self.get_failed_or_in_progress_subset(asset_key=child)
                            ):
                                result_asset_partitions.add(child_asset_partition)
                            else:
                                # manually query to see if this asset partition was intended to be
                                # executed in the same run as its parent
                                latest_partition_record = check.not_none(
                                    self.get_latest_materialization_or_observation_record(
                                        AssetKeyPartitionKey(asset_key, child_partition),
                                        after_cursor=latest_storage_id,
                                    )
                                )
                                if not self.is_asset_planned_for_run(
                                    latest_partition_record.run_id, child
                                ):
                                    result_asset_partitions.add(child_asset_partition)

            asset_latest_storage_id = self.get_latest_materialization_or_observation_storage_id(
                AssetKeyPartitionKey(asset_key)
            )
            if (
                result_latest_storage_id is None
                or (asset_latest_storage_id or 0) > result_latest_storage_id
            ):
                result_latest_storage_id = asset_latest_storage_id

        return (result_asset_partitions, result_latest_storage_id)

    ####################
    # RECONCILIATION
    ####################

    def _asset_partitions_data_versions(
        self,
        asset_key: AssetKey,
        asset_partitions: Optional[AbstractSet[AssetKeyPartitionKey]],
        after_cursor: Optional[int] = None,
        before_cursor: Optional[int] = None,
    ) -> Mapping[AssetKeyPartitionKey, Optional[DataVersion]]:
        if not self.asset_graph.is_partitioned(asset_key):
            asset_partition = AssetKeyPartitionKey(asset_key)
            latest_record = self.get_latest_materialization_or_observation_record(
                asset_partition, after_cursor=after_cursor, before_cursor=before_cursor
            )
            return (
                {asset_partition: extract_data_version_from_entry(latest_record.event_log_entry)}
                if latest_record is not None
                else {}
            )
        else:
            query_result = self.instance._event_storage.get_latest_tags_by_partition(  # noqa
                asset_key,
                event_type=self._event_type_for_key(asset_key),
                tag_keys=[DATA_VERSION_TAG],
                after_cursor=after_cursor,
                before_cursor=before_cursor,
                asset_partitions=(
                    [
                        asset_partition.partition_key
                        for asset_partition in asset_partitions
                        if asset_partition.partition_key is not None
                    ]
                    if asset_partitions is not None
                    else None
                ),
            )
            return {
                AssetKeyPartitionKey(asset_key, partition_key): (
                    DataVersion(tags[DATA_VERSION_TAG]) if tags.get(DATA_VERSION_TAG) else None
                )
                for partition_key, tags in query_result.items()
            }

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

        latest_versions = self._asset_partitions_data_versions(
            asset_key, to_query_asset_partitions, after_cursor=after_cursor
        )
        previous_versions = self._asset_partitions_data_versions(
            asset_key, to_query_asset_partitions, before_cursor=after_cursor + 1
        )
        queryed_updated_asset_partitions = {
            ap for ap, version in latest_versions.items() if previous_versions.get(ap) != version
        }
        # keep track of the maximum storage id at which an asset partition was updated after
        for asset_partition in queryed_updated_asset_partitions:
            self._asset_partition_versions_updated_after_cursor_cache[asset_partition] = (
                after_cursor
            )
        return {*updated_asset_partitions, *queryed_updated_asset_partitions}

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
            not self.asset_graph.is_source(asset_key) and not respect_materialization_data_versions
        ):
            return updated_after_cursor

        # more expensive check to explicitly handle data versions
        return self._asset_partition_versions_updated_after_cursor(
            asset_key, updated_after_cursor, after_cursor
        )

    def get_parent_asset_partitions_updated_after_child(
        self,
        asset_partition: AssetKeyPartitionKey,
        parent_asset_partitions: AbstractSet[AssetKeyPartitionKey],
        respect_materialization_data_versions: bool,
        ignored_parent_keys: AbstractSet[AssetKey],
    ) -> AbstractSet[AssetKeyPartitionKey]:
        """Returns values inside parent_asset_partitions that correspond to asset partitions that
        have been updated since the latest materialization of asset_partition.
        """
        parent_asset_partitions_by_key: Dict[AssetKey, Set[AssetKeyPartitionKey]] = defaultdict(set)
        for parent in parent_asset_partitions:
            parent_asset_partitions_by_key[parent.asset_key].add(parent)

        partitions_def = self.asset_graph.get_partitions_def(asset_partition.asset_key)
        updated_parents = set()

        for parent_key, parent_asset_partitions in parent_asset_partitions_by_key.items():
            # ignore updates to particular parents
            if parent_key in ignored_parent_keys:
                continue

            # ignore non-observable source parents
            if self.asset_graph.is_source(parent_key) and not self.asset_graph.is_observable(
                parent_key
            ):
                continue

            # when mapping from time or dynamic downstream to unpartitioned upstream, only check
            # for updates to the latest upstream partition
            if (
                isinstance(
                    partitions_def, (TimeWindowPartitionsDefinition, DynamicPartitionsDefinition)
                )
                and not self.asset_graph.is_partitioned(parent_key)
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

    def get_outdated_ancestors(
        self, *, asset_partition: AssetKeyPartitionKey
    ) -> AbstractSet[AssetKey]:
        """Return the set of assets that are ancestors of the given asset partition and have parents
        that have been updated more recently than they have.

        If two ancestors would be returned, but one of them is an ancestor of the other one, then
        only the most upstream ancestor is included.
        """
        if asset_partition in self._outdated_ancestors_cache:
            return self._outdated_ancestors_cache[asset_partition]

        if self.asset_graph.is_source(asset_partition.asset_key):
            return set()

        # First traverse upwards and gather any candidates that have not been previously added
        # to the cache
        visited: set[AssetKeyPartitionKey] = set()

        queue: deque[AssetKeyPartitionKey] = deque()
        queue.append(asset_partition)

        while queue:
            current_partition = queue.popleft()
            visited.add(current_partition)

            if self.asset_graph.is_source(current_partition.asset_key):
                continue

            parent_asset_partitions = self.asset_graph.get_parents_partitions(
                dynamic_partitions_store=self,
                current_time=self._evaluation_time,
                asset_key=current_partition.asset_key,
                partition_key=current_partition.partition_key,
            ).parent_partitions

            for parent in parent_asset_partitions:
                if (
                    parent not in visited
                    and parent not in self._outdated_ancestors_cache
                    # do not evaluate self-dependency asset partitions
                    and parent.asset_key != current_partition.asset_key
                ):
                    queue.append(parent)

        # Toposort them so that at each iteration we can count on the cache being full for
        # all of your parents, then update the cache for each node based on the parent's results
        toposort_queue = ToposortedPriorityQueue(
            self.asset_graph, visited, include_required_multi_assets=False
        )

        while len(toposort_queue) > 0:
            candidates_unit = toposort_queue.dequeue()
            for current_partition in candidates_unit:
                parent_asset_partitions = self.asset_graph.get_parents_partitions(
                    dynamic_partitions_store=self,
                    current_time=self._evaluation_time,
                    asset_key=current_partition.asset_key,
                    partition_key=current_partition.partition_key,
                ).parent_partitions

                updated_parents: AbstractSet[AssetKeyPartitionKey] = (
                    self.get_parent_asset_partitions_updated_after_child(
                        asset_partition=current_partition,
                        parent_asset_partitions=parent_asset_partitions,
                        respect_materialization_data_versions=self._respect_materialization_data_versions,
                        # ignore self-dependency asset partitions
                        ignored_parent_keys={current_partition.asset_key},
                    )
                )

                outdated_ancestors = {current_partition.asset_key} if updated_parents else set()

                for parent in set(parent_asset_partitions) - updated_parents:
                    outdated_ancestors.update(self._outdated_ancestors_cache.get(parent, set()))

                self._outdated_ancestors_cache[current_partition] = outdated_ancestors

        return self._outdated_ancestors_cache[asset_partition]
