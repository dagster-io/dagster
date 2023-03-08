import datetime
import json
from collections import defaultdict
from typing import (
    AbstractSet,
    Dict,
    Iterable,
    Mapping,
    Optional,
    Sequence,
    Tuple,
    Union,
    cast,
)

import dagster._check as check
from dagster._core.definitions.asset_graph import AssetGraph
from dagster._core.definitions.asset_selection import AssetSelection
from dagster._core.definitions.data_version import get_input_event_pointer_tag
from dagster._core.definitions.events import AssetKey, AssetKeyPartitionKey
from dagster._core.definitions.time_window_partitions import (
    TimeWindowPartitionsDefinition,
    TimeWindowPartitionsSubset,
)
from dagster._core.errors import DagsterInvariantViolationError
from dagster._core.event_api import EventRecordsFilter
from dagster._core.events import DagsterEventType
from dagster._core.instance import DagsterInstance, DynamicPartitionsStore
from dagster._core.storage.event_log import EventLogRecord, SqlEventLogStorage
from dagster._core.storage.event_log.base import AssetRecord
from dagster._core.storage.event_log.sql_event_log import AssetEventTagsTable
from dagster._core.storage.pipeline_run import (
    FINISHED_STATUSES,
    DagsterRun,
    DagsterRunStatus,
    RunRecord,
    RunsFilter,
)
from dagster._core.storage.tags import PARTITION_NAME_TAG
from dagster._core.utils import frozendict
from dagster._utils.cached_method import cached_method
from dagster._utils.merger import merge_dicts

USED_DATA_TAG = ".dagster/used_data"


class CachingInstanceQueryer(DynamicPartitionsStore):
    """Provides utility functions for querying for asset-materialization related data from the
    instance which will attempt to limit redundant expensive calls.

    Args:
        instance (DagsterInstance): The instance to query.
    """

    def __init__(self, instance: "DagsterInstance"):
        self._instance = instance

        self._latest_materialization_record_cache: Dict[AssetKeyPartitionKey, EventLogRecord] = {}
        # if we try to fetch the latest materialization record after a given cursor and don't find
        # anything, we can keep track of that fact, so that the next time try to fetch the latest
        # materialization record for a >= cursor, we don't need to query the instance
        self._no_materializations_after_cursor_cache: Dict[AssetKeyPartitionKey, int] = {}

        self._asset_record_cache: Dict[AssetKey, Optional[AssetRecord]] = {}
        self._asset_partition_count_cache: Dict[
            Optional[int], Dict[AssetKey, Mapping[str, int]]
        ] = defaultdict(dict)

        self._dynamic_partitions_cache: Dict[str, Sequence[str]] = {}

    @property
    def instance(self) -> "DagsterInstance":
        return self._instance

    def prefetch_for_keys(self, asset_keys: Sequence[AssetKey], after_cursor: Optional[int]):
        """For performance, batches together queries for selected assets"""
        asset_records = self.instance.get_asset_records(asset_keys)
        for asset_record in asset_records:
            self._asset_record_cache[asset_record.asset_entry.asset_key] = asset_record

        # based on those asset records, fill in our caches with values of the latest materailization
        # records per key
        for asset_key in asset_keys:
            # we just prefetched all the asset records, so if it's not in the cache, there are
            # no materializations for this key
            asset_record = self._asset_record_cache.get(asset_key)
            if asset_record is None:
                self._asset_record_cache[asset_key] = None

            last_materialization_record = (
                asset_record.asset_entry.last_materialization_record if asset_record else None
            )
            if asset_record is None or last_materialization_record is None:
                self._no_materializations_after_cursor_cache[
                    AssetKeyPartitionKey(asset_key=asset_key)
                ] = -1
            else:
                asset_partition = AssetKeyPartitionKey(
                    asset_key=asset_record.asset_entry.asset_key,
                    partition_key=last_materialization_record.partition_key,
                )

                self._latest_materialization_record_cache[
                    asset_partition
                ] = last_materialization_record
                self._no_materializations_after_cursor_cache[
                    asset_partition
                ] = last_materialization_record.storage_id

                # also cache the answer to queries that do not specify a partition
                self._latest_materialization_record_cache[
                    AssetKeyPartitionKey(asset_key=asset_key)
                ] = last_materialization_record
                self._no_materializations_after_cursor_cache[
                    AssetKeyPartitionKey(asset_key=asset_key)
                ] = last_materialization_record.storage_id

        # fill in the cache for partitioned assets
        self._asset_partition_count_cache[after_cursor] = dict(
            self._instance.get_materialization_count_by_partition(
                asset_keys=asset_keys,
                after_cursor=after_cursor,
            )
        )
        self._asset_partition_count_cache[None] = dict(
            self._instance.get_materialization_count_by_partition(
                asset_keys=asset_keys,
                after_cursor=None,
            )
        )

    def get_asset_record(self, asset_key: AssetKey) -> Optional[AssetRecord]:
        if asset_key not in self._asset_record_cache:
            self._asset_record_cache[asset_key] = next(
                iter(self.instance.get_asset_records([asset_key])), None
            )
        return self._asset_record_cache[asset_key]

    def is_asset_in_run(self, run_id: str, asset: Union[AssetKey, AssetKeyPartitionKey]) -> bool:
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

    def run_has_tag(self, run_id: str, tag_key: str, tag_value: str) -> bool:
        return cast(DagsterRun, self._get_run_by_id(run_id)).tags.get(tag_key) == tag_value

    def _get_run_by_id(self, run_id: str) -> Optional[DagsterRun]:
        run_record = self._get_run_record_by_id(run_id=run_id)
        if run_record is not None:
            return run_record.dagster_run
        return None

    @cached_method
    def _get_run_record_by_id(self, run_id: str) -> Optional[RunRecord]:
        return self._instance.get_run_record_by_id(run_id)

    @cached_method
    def _get_planned_materializations_for_run_from_events(
        self, run_id: str
    ) -> AbstractSet[AssetKey]:
        materializations_planned = self._instance.get_records_for_run(
            run_id=run_id, of_type=DagsterEventType.ASSET_MATERIALIZATION_PLANNED
        ).records
        return set(cast(AssetKey, record.asset_key) for record in materializations_planned)

    @cached_method
    def get_planned_materializations_for_run(self, run_id: str) -> AbstractSet[AssetKey]:
        run = self._get_run_by_id(run_id=run_id)
        if run is None:
            return set()

        if run.asset_selection:
            return run.asset_selection
        else:
            # must resort to querying the event log
            return self._get_planned_materializations_for_run_from_events(run_id=run_id)

    @cached_method
    def get_current_materializations_for_run(self, run_id: str) -> AbstractSet[AssetKey]:
        materializations = self._instance.get_records_for_run(
            run_id=run_id,
            of_type=DagsterEventType.ASSET_MATERIALIZATION,
        ).records
        return set(cast(AssetKey, record.asset_key) for record in materializations)

    @cached_method
    def _get_materialization_record(
        self,
        asset_partition: AssetKeyPartitionKey,
        after_cursor: Optional[int] = None,
        before_cursor: Optional[int] = None,
    ) -> Optional[EventLogRecord]:
        records = self._instance.get_event_records(
            EventRecordsFilter(
                event_type=DagsterEventType.ASSET_MATERIALIZATION,
                asset_key=asset_partition.asset_key,
                asset_partitions=[asset_partition.partition_key]
                if asset_partition.partition_key
                else None,
                after_cursor=after_cursor,
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
        if isinstance(asset, AssetKey):
            asset_partition = AssetKeyPartitionKey(asset_key=asset)
        else:
            asset_partition = asset

        # no materialization exists for this asset partition
        if (
            asset_partition.partition_key is not None
            and asset_partition.asset_key in self._asset_partition_count_cache[None]
            and asset_partition.partition_key
            not in self._asset_partition_count_cache[None][asset_partition.asset_key]
        ):
            return None

        if before_cursor is not None:
            latest_record = self._latest_materialization_record_cache.get(asset_partition)
            if latest_record is not None and latest_record.storage_id < before_cursor:
                return latest_record

            return self._get_materialization_record(
                asset_partition=asset_partition,
                after_cursor=after_cursor,
                before_cursor=before_cursor,
            )

        if asset_partition in self._latest_materialization_record_cache:
            cached_record = self._latest_materialization_record_cache[asset_partition]
            if after_cursor is None or after_cursor < cached_record.storage_id:
                return cached_record
            else:
                return None
        elif asset_partition in self._no_materializations_after_cursor_cache:
            if (after_cursor or 0) >= self._no_materializations_after_cursor_cache[asset_partition]:
                return None

        record = self._get_materialization_record(
            asset_partition=asset_partition, after_cursor=after_cursor, before_cursor=before_cursor
        )

        if record:
            self._latest_materialization_record_cache[asset_partition] = record
            return record
        else:
            if after_cursor is not None:
                self._no_materializations_after_cursor_cache[asset_partition] = min(
                    after_cursor,
                    self._no_materializations_after_cursor_cache.get(asset_partition, after_cursor),
                )
            return None

    def get_latest_materialization_records_by_key(
        self,
        asset_keys: Iterable[AssetKey],
        after_cursor: Optional[int] = None,
        before_cursor: Optional[int] = None,
    ) -> Mapping[AssetKey, "EventLogRecord"]:
        """
        Only returns entries for assets that have been materialized since the cursor.
        """
        result: Dict[AssetKey, "EventLogRecord"] = {}

        for asset_key in asset_keys:
            latest_record = self.get_latest_materialization_record(
                AssetKeyPartitionKey(asset_key),
                after_cursor=after_cursor,
                before_cursor=before_cursor,
            )
            if latest_record is not None:
                result[asset_key] = latest_record

        return result

    @cached_method
    def get_materialization_records(
        self,
        asset_key: AssetKey,
        after_cursor: Optional[int] = None,
        tags: Optional[Mapping[str, str]] = None,
    ) -> Iterable["EventLogRecord"]:
        return self._instance.get_event_records(
            EventRecordsFilter(
                event_type=DagsterEventType.ASSET_MATERIALIZATION,
                asset_key=asset_key,
                after_cursor=after_cursor,
                tags=tags,
            )
        )

    def get_materialized_partition_counts(
        self, asset_key: AssetKey, after_cursor: Optional[int] = None
    ) -> Mapping[str, int]:
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
        return [
            partition_key
            for partition_key, count in self.get_materialized_partition_counts(
                asset_key, after_cursor
            ).items()
            if count > 0
        ]

    @cached_method
    def is_reconciled(
        self,
        asset_partition: AssetKeyPartitionKey,
        asset_graph: AssetGraph,
    ) -> bool:
        """
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


    def get_latest_storage_id(self, event_type: DagsterEventType) -> Optional[int]:
        """
        Returns None if there are no events from that type in the event log.
        """
        records = list(
            self.instance.get_event_records(
                event_records_filter=EventRecordsFilter(event_type=event_type), limit=1
            )
        )
        if records:
            return records[0].storage_id
        else:
            return None

    def get_dynamic_partitions(self, partitions_def_name: str) -> Sequence[str]:
        if partitions_def_name in self._dynamic_partitions_cache:
            return self._dynamic_partitions_cache[partitions_def_name]

        self._dynamic_partitions_cache[partitions_def_name] = self.instance.get_dynamic_partitions(
            partitions_def_name
        )
        return self._dynamic_partitions_cache[partitions_def_name]
