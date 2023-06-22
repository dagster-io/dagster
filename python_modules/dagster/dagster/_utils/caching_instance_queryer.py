from collections import defaultdict
from datetime import datetime
from typing import (
    TYPE_CHECKING,
    AbstractSet,
    Dict,
    Iterable,
    Mapping,
    Optional,
    Sequence,
    Union,
    cast,
)

import pendulum

import dagster._check as check
from dagster._core.definitions.asset_graph import AssetGraph
from dagster._core.definitions.data_version import (
    DataVersion,
    extract_data_version_from_entry,
)
from dagster._core.definitions.events import AssetKey, AssetKeyPartitionKey
from dagster._core.definitions.partition import DynamicPartitionsDefinition
from dagster._core.definitions.time_window_partitions import TimeWindowPartitionsDefinition
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
    ):
        self._instance = instance
        self._asset_graph = asset_graph

        self._asset_record_cache: Dict[AssetKey, Optional[AssetRecord]] = {}
        self._latest_materialization_record_cache: Dict[
            AssetKeyPartitionKey, Optional[EventLogRecord]
        ] = {}

        self._asset_partition_count_cache: Dict[
            Optional[int], Dict[AssetKey, Mapping[str, int]]
        ] = defaultdict(dict)

        self._dynamic_partitions_cache: Dict[str, Sequence[str]] = {}

        self._evaluation_time = evaluation_time if evaluation_time else pendulum.now("UTC")

    @property
    def instance(self) -> DagsterInstance:
        return self._instance

    @property
    def asset_graph(self) -> AssetGraph:
        return self._asset_graph

    ####################
    # QUERY BATCHING
    ####################

    def prefetch_asset_partition_counts(
        self, asset_keys: Sequence[AssetKey], after_cursor: Optional[int]
    ):
        """For performance, batches together queries for selected assets."""
        if after_cursor is not None:
            self._asset_partition_count_cache[after_cursor] = dict(
                self.instance.get_materialization_count_by_partition(
                    asset_keys=asset_keys,
                    after_cursor=after_cursor,
                )
            )

    def prefetch_asset_records(self, asset_keys: Sequence[AssetKey]):
        """For performance, batches together queries for selected assets."""
        # get all asset records for the selected assets
        asset_records = self.instance.get_asset_records(asset_keys)
        for asset_record in asset_records:
            self._asset_record_cache[asset_record.asset_entry.asset_key] = asset_record

        for asset_key in asset_keys:
            # if an asset has no materializations, it may not have an asset record
            asset_record = self._asset_record_cache.get(asset_key)
            if asset_record is None:
                self._asset_record_cache[asset_key] = None

            # use the asset record to determine the latest materialization record
            latest_materialization_record = (
                asset_record.asset_entry.last_materialization_record if asset_record else None
            )
            self._latest_materialization_record_cache[
                AssetKeyPartitionKey(asset_key=asset_key)
            ] = latest_materialization_record

            # if we have a latest materialization record, then we also know what partition this
            # record was associated with (if any)
            if latest_materialization_record is not None:
                self._latest_materialization_record_cache[
                    AssetKeyPartitionKey(
                        asset_key=asset_key,
                        partition_key=latest_materialization_record.partition_key,
                    )
                ] = latest_materialization_record

    ####################
    # MATERIALIZATION / ASSET RECORDS
    ####################

    def get_asset_record(self, asset_key: AssetKey) -> Optional["AssetRecord"]:
        if asset_key not in self._asset_record_cache:
            self._asset_record_cache[asset_key] = next(
                iter(self.instance.get_asset_records([asset_key])), None
            )
        return self._asset_record_cache[asset_key]

    @cached_method
    def _get_latest_record(
        self, *, asset_partition: AssetKeyPartitionKey, before_cursor: Optional[int] = None
    ) -> Optional["EventLogRecord"]:
        from dagster._core.event_api import EventRecordsFilter

        records = self.instance.get_event_records(
            EventRecordsFilter(
                event_type=self._event_type_for_key(asset_partition.asset_key),
                asset_key=asset_partition.asset_key,
                asset_partitions=[asset_partition.partition_key]
                if asset_partition.partition_key
                else None,
                before_cursor=before_cursor,
            ),
            ascending=False,
            limit=1,
        )
        return next(iter(records), None)

    def materialization_exists(
        self,
        asset_partition: AssetKeyPartitionKey,
        after_cursor: Optional[int] = None,
    ) -> bool:
        """Returns True if there is a materialization record for the given asset partition after
        the specified cursor. Because this function does not need to return the actual record, it
        is more efficient than get_latest_materialization_record when partitioned assets involved.

        Args:
            asset_partition (AssetKeyPartitionKey): The asset partition to query.
            after_cursor (Optional[int]): Filter parameter such that only records with a storage_id
                greater than this value will be considered.
        """
        return (self.get_latest_storage_id(asset_partition) or 0) > (after_cursor or 0)

    def get_latest_materialization_record(
        self,
        asset: Union[AssetKey, AssetKeyPartitionKey],
        after_cursor: Optional[int] = None,
        before_cursor: Optional[int] = None,
    ) -> Optional["EventLogRecord"]:
        """Returns the latest record for the given asset partition given the specified cursors.

        Args:
            asset (Union[AssetKey, AssetKeyPartitionKey]): The asset (partition) to query.
            after_cursor (Optional[int]): Filter parameter such that only records with a storage_id
                greater than this value will be considered.
            before_cursor (Optional[int]): Filter parameter such that only records with a storage_id
                less than this value will be considered.
        """
        if isinstance(asset, AssetKey):
            asset_partition = AssetKeyPartitionKey(asset_key=asset)
        else:
            asset_partition = asset

        check.param_invariant(
            not (after_cursor and before_cursor),
            "before_cursor",
            "Cannot set both before_cursor and after_cursor",
        )

        latest_storage_id = self.get_latest_storage_id(asset_partition)
        if latest_storage_id is None or (latest_storage_id <= (after_cursor or 0)):
            return None
        return self._get_latest_record(asset_partition=asset_partition, before_cursor=before_cursor)

    @cached_method
    def get_materialization_records(
        self,
        *,
        asset_key: AssetKey,
        after_cursor: Optional[int] = None,
        tags: Optional[Mapping[str, str]] = None,
    ) -> Iterable["EventLogRecord"]:
        from dagster._core.event_api import EventRecordsFilter

        return self.instance.get_event_records(
            EventRecordsFilter(
                event_type=DagsterEventType.ASSET_MATERIALIZATION,
                asset_key=asset_key,
                after_cursor=after_cursor,
                tags=tags,
            )
        )

    ####################
    # OBSERVATIONS
    ####################

    @cached_method
    def get_observation_record(
        self,
        *,
        asset_key: AssetKey,
        before_cursor: Optional[int],
    ) -> Optional["EventLogRecord"]:
        from dagster._core.event_api import EventRecordsFilter

        return next(
            iter(
                self.instance.get_event_records(
                    EventRecordsFilter(
                        event_type=DagsterEventType.ASSET_OBSERVATION,
                        asset_key=asset_key,
                        before_cursor=before_cursor,
                    ),
                    ascending=False,
                )
            ),
            None,
        )

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

    def new_version_storage_id(
        self,
        observable_source_asset_key: AssetKey,
        after_cursor: Optional[int] = None,
    ) -> Optional[int]:
        """Returns the storage id of the latest asset observation if it is a different version
        from the latest observation before the cursor, or None if no such observation exists.

        Args:
            observable_source_asset_key (AssetKeyPartitionKey): The observable source asset to query.
            after_cursor (Optional[int]): Filter parameter such that only records with a storage_id
                greater than this value will be considered.
        """
        previous_version_record = (
            self.get_observation_record(
                asset_key=observable_source_asset_key,
                # we're looking for if a new version exists after `after_cursor`, so we need to know
                # what the version was before `after_cursor`
                before_cursor=after_cursor,
            )
            # if the after_cursor is None, then no previous version can exist
            if after_cursor is not None
            else None
        )
        previous_version = (
            extract_data_version_from_entry(previous_version_record.event_log_entry)
            if previous_version_record is not None
            else None
        )

        latest_version_record = self.get_observation_record(
            asset_key=observable_source_asset_key,
            before_cursor=None,
        )
        if (
            latest_version_record is None
            or extract_data_version_from_entry(latest_version_record.event_log_entry)
            == previous_version
        ):
            return None
        return (
            latest_version_record.storage_id
            if after_cursor is None or latest_version_record.storage_id > after_cursor
            else None
        )

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

        if run.asset_selection:
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
    # PARTITIONS
    ####################

    def get_materialized_partition_counts(
        self, asset_key: AssetKey, after_cursor: Optional[int] = None
    ) -> Mapping[str, int]:
        """Returns a mapping from partition key to the number of times that partition has been
        materialized for a given asset.

        Args:
            asset_key (AssetKey): The asset key.
            after_cursor (Optional[int]): The cursor after which to look for materializations. If
                not provided, will look at all materializations.
        """
        if (
            after_cursor not in self._asset_partition_count_cache
            or asset_key not in self._asset_partition_count_cache[after_cursor]
        ):
            self._asset_partition_count_cache[after_cursor][
                asset_key
            ] = self.instance.get_materialization_count_by_partition(
                asset_keys=[asset_key], after_cursor=after_cursor
            )[
                asset_key
            ]
        return self._asset_partition_count_cache[after_cursor][asset_key]

    def get_materialized_partitions(
        self, asset_key: AssetKey, after_cursor: Optional[int] = None
    ) -> Iterable[str]:
        """Returns a list of the partitions that have been materialized for the given asset key.

        Args:
            asset_key (AssetKey): The asset key.
            after_cursor (Optional[int]): The cursor after which to look for materializations. If
                not provided, will look at all materializations.
        """
        return [
            partition_key
            for partition_key, count in self.get_materialized_partition_counts(
                asset_key, after_cursor
            ).items()
            if count > 0
        ]

    def get_dynamic_partitions(self, partitions_def_name: str) -> Sequence[str]:
        """Returns a list of partitions for a partitions definition."""
        if partitions_def_name not in self._dynamic_partitions_cache:
            self._dynamic_partitions_cache[
                partitions_def_name
            ] = self.instance.get_dynamic_partitions(partitions_def_name)
        return self._dynamic_partitions_cache[partitions_def_name]

    def has_dynamic_partition(self, partitions_def_name: str, partition_key: str) -> bool:
        return partition_key in self.get_dynamic_partitions(partitions_def_name)

    ####################
    # RECONCILIATION
    ####################

    def get_latest_storage_id_for_event_type(self, event_type: DagsterEventType) -> Optional[int]:
        """Returns the latest storage id for an event of the given event type. If no such event
        exists, returns None.

        Args:
            event_type (DagsterEventType): The event type to search for.
        """
        from dagster._core.event_api import EventRecordsFilter

        records = list(
            self.instance.get_event_records(
                event_records_filter=EventRecordsFilter(event_type=event_type), limit=1
            )
        )
        if records:
            return records[0].storage_id
        else:
            return None

    @cached_method
    def is_reconciled(
        self,
        *,
        asset_partition: AssetKeyPartitionKey,
        asset_graph: AssetGraph,
    ) -> bool:
        """Returns a boolean representing if the given `asset_partition` is currently reconciled.
        An asset (partition) is considered unreconciled if any of:
        - It has never been materialized
        - One of its parents has been updated more recently than it has
        - One of its parents is unreconciled.
        """
        # always treat source assets as reconciled
        if asset_graph.is_source(asset_partition.asset_key):
            return True

        if not self.materialization_exists(asset_partition):
            return False

        time_or_dynamic_partitioned = isinstance(
            asset_graph.get_partitions_def(asset_partition.asset_key),
            (TimeWindowPartitionsDefinition, DynamicPartitionsDefinition),
        )

        for parent in asset_graph.get_parents_partitions(
            dynamic_partitions_store=self,
            current_time=self._evaluation_time,
            asset_key=asset_partition.asset_key,
            partition_key=asset_partition.partition_key,
        ).parent_partitions:
            # when mapping from time or dynamic downstream to unpartitioned upstream, only check
            # for existence of upstream materialization, do not worry about timestamps
            if time_or_dynamic_partitioned and parent.partition_key is None:
                return (
                    # no materializations exist for source assets
                    asset_graph.is_source(parent.asset_key)
                    or self.materialization_exists(parent)
                )

            if asset_graph.is_source(parent.asset_key) and not asset_graph.is_observable(
                parent.asset_key
            ):
                continue
            # TODO: this should always factor in data versions
            elif not self.child_has_updated_parent(
                child=asset_partition,
                parent=parent,
                # for now, only check data versions for observable source assets
                use_data_versions=asset_graph.is_observable(parent.asset_key),
            ):
                return False
            elif not self.is_reconciled(asset_partition=parent, asset_graph=asset_graph):
                return False

        return True

    @property
    def evaluation_time(self) -> datetime:
        return self._evaluation_time

    ####################
    # SCRATCH
    ####################

    def _event_type_for_key(self, asset_key: AssetKey) -> DagsterEventType:
        if self.asset_graph.is_source(asset_key):
            return DagsterEventType.ASSET_OBSERVATION
        else:
            return DagsterEventType.ASSET_MATERIALIZATION

    @cached_method
    def get_latest_storage_ids(self, *, asset_key: AssetKey) -> Mapping[AssetKeyPartitionKey, int]:
        if self.asset_graph.is_partitioned(asset_key):
            latest_storage_ids = {
                AssetKeyPartitionKey(asset_key, partition_key): storage_id
                for partition_key, storage_id in self.instance.get_latest_storage_id_by_partition(
                    asset_key, event_type=self._event_type_for_key(asset_key)
                ).items()
            }
            # also handle the case where you want to know the latest overall storage_id for the
            # partitioned asset
            if latest_storage_ids:
                latest_storage_ids[AssetKeyPartitionKey(asset_key)] = max(
                    latest_storage_ids.values()
                )
            return latest_storage_ids
        elif self.asset_graph.is_source(asset_key):
            observation_record = self.get_observation_record(
                asset_key=asset_key, before_cursor=None
            )
            if observation_record is None:
                return {}
            return {AssetKeyPartitionKey(asset_key): observation_record.storage_id}
        else:
            asset_record = self.get_asset_record(asset_key)
            if asset_record is None or asset_record.asset_entry.last_materialization_record is None:
                return {}
            return {
                AssetKeyPartitionKey(
                    asset_key
                ): asset_record.asset_entry.last_materialization_record.storage_id
            }

    def get_latest_storage_id(self, asset_partition: AssetKeyPartitionKey) -> Optional[int]:
        return self.get_latest_storage_ids(asset_key=asset_partition.asset_key).get(asset_partition)

    def has_updated_version(
        self,
        asset_partition: AssetKeyPartitionKey,
        after_cursor: int,
    ) -> bool:
        # note: this is a placeholder method that is inefficient but terse, to make it easier to
        # review this diff in isolation. child_has_updated_parent will be replaced with a more efficient
        # implementation that batches multiple partitions into a single query
        latest_record = self.get_latest_materialization_record(
            asset_partition, after_cursor=after_cursor
        )
        previous_record = self.get_latest_materialization_record(
            asset_partition, before_cursor=after_cursor
        )
        if latest_record is None:
            return False
        elif previous_record is None:
            return True
        return extract_data_version_from_entry(
            latest_record.event_log_entry
        ) != extract_data_version_from_entry(previous_record.event_log_entry)

    def child_has_updated_parent(
        self, child: AssetKeyPartitionKey, parent: AssetKeyPartitionKey, use_data_versions: bool
    ) -> bool:
        """Returns True if the child was materialized after the parent."""
        child_storage_id = self.get_latest_storage_id(child)
        parent_storage_id = self.get_latest_storage_id(parent)

        if child_storage_id is None or child_storage_id > (parent_storage_id or 0):
            return True
        # if not factoring in data versions, we're done
        elif not use_data_versions:
            return False
        return not self.has_updated_version(parent, after_cursor=child_storage_id)
