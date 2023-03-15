from collections import defaultdict
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

import dagster._check as check
from dagster._core.definitions.asset_graph import AssetGraph
from dagster._core.definitions.events import AssetKey, AssetKeyPartitionKey
from dagster._core.events import DagsterEventType
from dagster._core.instance import DagsterInstance, DynamicPartitionsStore
from dagster._core.storage.pipeline_run import (
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

    def __init__(self, instance: DagsterInstance):
        self._instance = instance

        self._asset_record_cache: Dict[AssetKey, Optional[AssetRecord]] = {}
        self._latest_materialization_record_cache: Dict[
            AssetKeyPartitionKey, Optional[EventLogRecord]
        ] = {}

        self._asset_partition_count_cache: Dict[
            Optional[int], Dict[AssetKey, Mapping[str, int]]
        ] = defaultdict(dict)

        self._dynamic_partitions_cache: Dict[str, Sequence[str]] = {}

    @property
    def instance(self) -> DagsterInstance:
        return self._instance

    ####################
    # QUERY BATCHING
    ####################

    def prefetch_asset_partition_counts(
        self, asset_keys: Sequence[AssetKey], after_cursor: Optional[int]
    ):
        """For performance, batches together queries for selected assets."""
        self._asset_partition_count_cache[None] = dict(
            self.instance.get_materialization_count_by_partition(
                asset_keys=asset_keys,
                after_cursor=None,
            )
        )
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
    def _get_latest_materialization_record(
        self, *, asset_partition: AssetKeyPartitionKey, before_cursor: Optional[int] = None
    ) -> Optional["EventLogRecord"]:
        from dagster._core.event_api import EventRecordsFilter

        records = self.instance.get_event_records(
            EventRecordsFilter(
                event_type=DagsterEventType.ASSET_MATERIALIZATION,
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

    def get_latest_materialization_record(
        self,
        asset: Union[AssetKey, AssetKeyPartitionKey],
        after_cursor: Optional[int] = None,
        before_cursor: Optional[int] = None,
    ) -> Optional["EventLogRecord"]:
        """Returns the latest materialization record for the given asset partition between the
        specified cursors.

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

        # the count of this (asset key, partition key) pair is 0
        if (
            asset_partition.partition_key is not None
            and after_cursor in self._asset_partition_count_cache
            and asset_partition.asset_key in self._asset_partition_count_cache[after_cursor]
            and self._asset_partition_count_cache[after_cursor][asset_partition.asset_key].get(
                asset_partition.partition_key, 0
            )
            == 0
        ):
            return None

        # ensure we know the latest overall materialization record for this asset partition
        if asset_partition not in self._latest_materialization_record_cache:
            self._latest_materialization_record_cache[
                asset_partition
            ] = self._get_latest_materialization_record(
                asset_partition=asset_partition,
            )

        # the latest overall record
        latest_record = self._latest_materialization_record_cache[asset_partition]

        # there are no records for this asset partition after after_cursor
        if latest_record is None or latest_record.storage_id <= (after_cursor or 0):
            return None

        if before_cursor is None:
            return latest_record
        else:
            if latest_record is None:
                # no records exist
                return None
            elif latest_record.storage_id < before_cursor:
                # the latest record is before the cursor, so we can return it
                return latest_record
            else:
                # fall back to an explicit query
                return self._get_latest_materialization_record(
                    asset_partition=asset_partition, before_cursor=before_cursor
                )

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
            check.failed("")

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

    ####################
    # RECONCILIATION
    ####################

    def get_latest_storage_id(self, event_type: DagsterEventType) -> Optional[int]:
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
        self, *, asset_partition: AssetKeyPartitionKey, asset_graph: AssetGraph
    ) -> bool:
        """Returns a boolean representing if the given `asset_partition` is currently reconciled.
        An asset (partition) is considered unreconciled if any of:
        - It has never been materialized
        - One of its parents has been updated more recently than it has
        - One of its parents is unreconciled.
        """
        latest_materialization_record = self.get_latest_materialization_record(
            asset_partition, None
        )

        if latest_materialization_record is None:
            return False

        for parent in asset_graph.get_parents_partitions(
            self,
            asset_partition.asset_key,
            asset_partition.partition_key,
        ):
            if asset_graph.is_source(parent.asset_key):
                continue

            if (
                self.get_latest_materialization_record(
                    parent, after_cursor=latest_materialization_record.storage_id
                )
                is not None
            ):
                return False

            if not self.is_reconciled(asset_partition=parent, asset_graph=asset_graph):
                return False

        return True
