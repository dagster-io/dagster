import datetime
import json
from typing import TYPE_CHECKING, AbstractSet, Dict, Iterable, Mapping, Optional, Tuple, Union, cast

import dagster._check as check
from dagster._core.definitions.asset_graph import AssetGraph
from dagster._core.definitions.events import AssetKey, AssetKeyPartitionKey
from dagster._core.errors import DagsterInvariantViolationError
from dagster._core.storage.event_log import EventLogRecord, SqlEventLogStorage
from dagster._core.storage.event_log.sql_event_log import AssetEventTagsTable
from dagster._core.storage.pipeline_run import (
    IN_PROGRESS_RUN_STATUSES,
    DagsterRun,
    RunRecord,
    RunsFilter,
)
from dagster._core.storage.tags import PARTITION_NAME_TAG
from dagster._utils.cached_method import cached_method
from dagster._utils.merger import merge_dicts

if TYPE_CHECKING:
    from dagster import DagsterInstance

USED_DATA_TAG = ".dagster/used_data"


class CachingInstanceQueryer:
    """Provides utility functions for querying for asset-materialization related data from the
    instance which will attempt to limit redundant expensive calls."""

    def __init__(self, instance: "DagsterInstance"):
        self._instance = instance

        self._latest_materialization_record_cache: Dict[AssetKeyPartitionKey, EventLogRecord] = {}
        # if we try to fetch the latest materialization record after a given cursor and don't find
        # anything, we can keep track of that fact, so that the next time try to fetch the latest
        # materialization record for a >= cursor, we don't need to query the instance
        self._no_materializations_after_cursor_cache: Dict[AssetKeyPartitionKey, int] = {}

    def get_in_progress_run_time_and_planned_materializations(
        self, asset_key: AssetKey
    ) -> Tuple[Optional[datetime.datetime], AbstractSet[AssetKey]]:
        # the latest asset record is updated when the run is created
        asset_records = self._instance.get_asset_records([asset_key])
        asset_record = next(iter(asset_records), None)
        if asset_record is None or asset_record.asset_entry.last_run_id is None:
            return (None, set())
        run_id = asset_record.asset_entry.last_run_id

        run_record = self._get_run_record_by_id(run_id=run_id)
        if run_record is not None and run_record.pipeline_run.status in IN_PROGRESS_RUN_STATUSES:
            data_time = (
                datetime.datetime.fromtimestamp(run_record.start_time, tz=datetime.timezone.utc)
                if run_record.start_time
                else None
            )
            return (data_time, self._get_planned_materializations_for_run(run_id=run_id))
        return (None, set())

    def is_asset_partition_in_run(self, run_id: str, asset_partition: AssetKeyPartitionKey) -> bool:
        run = self._get_run_by_id(run_id=run_id)
        if not run:
            check.failed("")

        if run.tags.get(PARTITION_NAME_TAG) != asset_partition.partition_key:
            return False

        if run.asset_selection:
            return asset_partition.asset_key in run.asset_selection
        else:
            return asset_partition.asset_key in self._get_planned_materializations_for_run(
                run_id=run_id
            )

    def _get_run_by_id(self, run_id: str) -> Optional[DagsterRun]:
        run_record = self._get_run_record_by_id(run_id=run_id)
        if run_record is not None:
            return run_record.pipeline_run
        return None

    @cached_method
    def _get_run_record_by_id(self, run_id: str) -> Optional[RunRecord]:
        return next(
            iter(self._instance.get_run_records(filters=RunsFilter(run_ids=[run_id]), limit=1)),
            None,
        )

    @cached_method
    def _get_planned_materializations_for_run(self, run_id: str) -> AbstractSet[AssetKey]:
        from dagster._core.events import DagsterEventType

        materializations_planned = self._instance.get_records_for_run(
            run_id=run_id,
            of_type=DagsterEventType.ASSET_MATERIALIZATION_PLANNED,
        ).records
        return set(cast(AssetKey, record.asset_key) for record in materializations_planned)

    @cached_method
    def _get_materialization_record(
        self,
        asset_partition: AssetKeyPartitionKey,
        after_cursor: Optional[int] = None,
        before_cursor: Optional[int] = None,
    ) -> Optional[EventLogRecord]:
        from dagster import DagsterEventType, EventRecordsFilter

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

        if asset_partition in self._latest_materialization_record_cache:
            cached_record = self._latest_materialization_record_cache[asset_partition]
            if (after_cursor is None or after_cursor < cached_record.storage_id) and (
                before_cursor is None or before_cursor > cached_record.storage_id
            ):
                return cached_record
            else:
                return None
        elif asset_partition in self._no_materializations_after_cursor_cache:
            if (
                after_cursor is not None
                and after_cursor >= self._no_materializations_after_cursor_cache[asset_partition]
            ):
                return None

        record = self._get_materialization_record(
            asset_partition=asset_partition, after_cursor=after_cursor, before_cursor=before_cursor
        )

        if record:
            self._latest_materialization_record_cache[asset_partition] = record
            return record
        else:
            if after_cursor is not None and before_cursor is None:
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
    def is_reconciled(
        self,
        asset_partition: AssetKeyPartitionKey,
        asset_graph: AssetGraph,
    ) -> bool:
        """
        An asset (partition) is considered unreconciled if any of:
        - It has never been materialized
        - One of its parents has been updated more recently than it has
        - One of its parents is unreconciled
        """
        latest_materialization_record = self.get_latest_materialization_record(
            asset_partition, None
        )

        if latest_materialization_record is None:
            return False

        for parent in asset_graph.get_parents_partitions(
            asset_partition.asset_key, asset_partition.partition_key
        ):
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

    def set_known_used_data(
        self,
        record: EventLogRecord,
        new_known_data: Dict[AssetKey, Tuple[Optional[int], Optional[float]]],
    ):
        event_log_storage = self._instance.event_log_storage
        if (
            event_log_storage.supports_add_asset_event_tags()
            and record.asset_key is not None
            and record.storage_id is not None
            and record.event_log_entry.timestamp is not None
        ):
            current_known_data = self.get_known_used_data(record.asset_key, record.storage_id)
            known_data = merge_dicts(current_known_data, new_known_data)
            serialized_times = json.dumps(
                {key.to_user_string(): value for key, value in known_data.items()}
            )
            event_log_storage.add_asset_event_tags(
                event_id=record.storage_id,
                event_timestamp=record.event_log_entry.timestamp,
                asset_key=record.asset_key,
                new_tags={USED_DATA_TAG: serialized_times},
            )

    def get_known_used_data(
        self, asset_key: AssetKey, record_id: int
    ) -> Dict[AssetKey, Tuple[Optional[int], Optional[float]]]:
        """Returns the known upstream ids and timestamps stored on the instance"""
        event_log_storage = self._instance.event_log_storage
        if isinstance(event_log_storage, SqlEventLogStorage) and event_log_storage.has_table(
            AssetEventTagsTable.name
        ):
            # attempt to fetch from the instance asset event tags
            tags_list = event_log_storage.get_event_tags_for_asset(
                asset_key=asset_key, filter_event_id=record_id
            )
            if len(tags_list) == 0:
                return {}

            serialized_times = tags_list[0].get(USED_DATA_TAG, "{}")
            return {
                AssetKey.from_user_string(key): tuple(value)  # type:ignore
                for key, value in json.loads(serialized_times).items()
            }
        return {}

    @cached_method
    def calculate_used_data(
        self,
        asset_graph: AssetGraph,
        asset_key: AssetKey,
        record_id: Optional[int],
        record_timestamp: Optional[float],
        required_keys: AbstractSet[AssetKey],
    ) -> Dict[AssetKey, Tuple[Optional[int], Optional[float]]]:

        if record_id is None:
            return {key: (None, None) for key in required_keys}

        # grab the existing upstream data times already calculated for this record (if any)
        known_data = self.get_known_used_data(asset_key, record_id)
        if asset_key in required_keys:
            known_data[asset_key] = (record_id, record_timestamp)

        # not all required keys have known values
        unknown_required_keys = required_keys - set(known_data.keys())
        if unknown_required_keys:

            # find the upstream times of each of the parents of this asset
            for parent_key in asset_graph.get_parents(asset_key):
                if parent_key in asset_graph.source_asset_keys:
                    continue

                # the set of required keys which are upstream of this parent
                upstream_required_keys = set()
                if parent_key in unknown_required_keys:
                    upstream_required_keys.add(parent_key)
                for upstream_key in asset_graph.upstream_key_iterator(parent_key):
                    if upstream_key in unknown_required_keys:
                        upstream_required_keys.add(upstream_key)

                # get the most recent asset materialization for this parent which happened before
                # the current record
                latest_parent_record = self.get_latest_materialization_record(
                    parent_key, before_cursor=record_id
                )

                # recurse to find the data times of this parent
                for key, tup in self.calculate_used_data(
                    asset_graph=asset_graph,
                    asset_key=parent_key,
                    record_id=latest_parent_record.storage_id if latest_parent_record else None,
                    record_timestamp=latest_parent_record.event_log_entry.timestamp
                    if latest_parent_record
                    else None,
                    required_keys=frozenset(upstream_required_keys),
                ).items():
                    # if root data is missing, this overrides other values
                    if tup == (None, None) or known_data.get(key) == (None, None):
                        known_data[key] = (None, None)
                    else:
                        known_data[key] = min(known_data.get(key, tup), tup)

        return {k: v for k, v in known_data.items() if k in required_keys}

    def get_used_data_times_for_record(
        self,
        asset_graph: AssetGraph,
        record: EventLogRecord,
        upstream_keys: Optional[AbstractSet[AssetKey]] = None,
    ) -> Mapping[AssetKey, Optional[datetime.datetime]]:
        """Method to enable calculating the timestamps of materializations of upstream assets
        which were relevant to a given AssetMaterialization. These timestamps can be calculated relative
        to any upstream asset keys.

        The heart of this functionality is a recursive method which takes a given asset materialization
        and finds the most recent materialization of each of its parents which happened *before* that
        given materialization event.
        """
        if record.asset_key is None:
            raise DagsterInvariantViolationError(
                "Can only calculate data times for records with an `asset_key`."
            )
        if upstream_keys is None:
            upstream_keys = asset_graph.get_non_source_roots(record.asset_key)

        data = self.calculate_used_data(
            asset_graph=asset_graph,
            asset_key=record.asset_key,
            record_id=record.storage_id,
            record_timestamp=record.event_log_entry.timestamp,
            required_keys=frozenset(upstream_keys),
        )
        self.set_known_used_data(record, new_known_data=data)

        return {
            key: datetime.datetime.fromtimestamp(timestamp, tz=datetime.timezone.utc)
            if timestamp is not None
            else None
            for key, (_, timestamp) in data.items()
        }

    def get_current_minutes_late_for_key(
        self,
        evaluation_time: datetime.datetime,
        asset_graph: AssetGraph,
        asset_key: AssetKey,
    ) -> Optional[float]:
        freshness_policy = asset_graph.freshness_policies_by_key.get(asset_key)
        if freshness_policy is None:
            raise DagsterInvariantViolationError(
                "Cannot calculate minutes late for asset without a FreshnessPolicy"
            )

        latest_record = self.get_latest_materialization_record(asset_key)
        if latest_record is None:
            return None

        used_data_times = self.get_used_data_times_for_record(asset_graph, latest_record)

        return freshness_policy.minutes_late(
            evaluation_time=evaluation_time,
            used_data_times=used_data_times,
            available_data_times={key: evaluation_time for key in used_data_times},
        )
