import datetime
from typing import AbstractSet, Dict, Mapping, Optional, Sequence, Tuple

import dagster._check as check
from dagster._core.definitions.asset_graph import AssetGraph
from dagster._core.definitions.asset_selection import AssetSelection
from dagster._core.definitions.data_version import get_input_event_pointer_tag
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.time_window_partitions import (
    TimeWindowPartitionsDefinition,
    TimeWindowPartitionsSubset,
)
from dagster._core.errors import DagsterInvariantViolationError
from dagster._core.event_api import EventLogRecord
from dagster._core.instance import DagsterInstance
from dagster._core.storage.pipeline_run import FINISHED_STATUSES, DagsterRunStatus, RunsFilter
from dagster._utils import frozendict
from dagster._utils.cached_method import cached_method
from dagster._utils.caching_instance_queryer import CachingInstanceQueryer


class CachingDataTimeResolver:
    _instance_queryer: CachingInstanceQueryer

    def __init__(self, instance_queryer: CachingInstanceQueryer):
        self._instance_queryer = instance_queryer

    @property
    def instance(self) -> DagsterInstance:
        return self._instance_queryer.instance

    @property
    def instance_queryer(self) -> CachingInstanceQueryer:
        return self._instance_queryer

    def _calculate_time_partitioned_asset_data_time(
        self,
        asset_key: AssetKey,
        asset_graph: AssetGraph,
        cursor: int,
        partitions_def: TimeWindowPartitionsDefinition,
    ) -> Optional[datetime.datetime]:
        """Returns the time up until which all available data has been consumed for this asset.

        At a high level, this algorithm works as follows:

        First, calculate the subset of partitions that have been materialized up until this point
        in time (ignoring the cursor). This is done by querying the asset status cache if it is
        available, otherwise by using a (slower) get_materialization_count_by_partition query.

        Next, we calculate the set of partitions that are net-new since the cursor. This is done by
        comparing the count of materializations before after the cursor to the total count of
        materializations.

        Finally, we calculate the minimum time window of the net-new partitions. This time window
        did not exist at the time of the cursor, so we know that we have all data up until the
        beginning of that time window, or all data up until the end of the first filled time window
        in the total set, whichever is less.
        """
        from dagster._core.storage.partition_status_cache import (
            get_and_update_asset_status_cache_value,
        )

        if self.instance.can_cache_asset_status_data():
            # this is the current state of the asset, not the state of the asset at the time of record_id
            status_cache_value = get_and_update_asset_status_cache_value(
                instance=self.instance,
                asset_key=asset_key,
                partitions_def=partitions_def,
            )
            partition_subset = (
                status_cache_value.deserialize_materialized_partition_subsets(
                    partitions_def=partitions_def
                )
                if status_cache_value
                else partitions_def.empty_subset()
            )
        else:
            # if we can't use the asset status cache, then we get the subset by querying for the
            # existing partitions
            partition_subset = partitions_def.empty_subset().with_partition_keys(
                self._instance_queryer.get_materialized_partitions(asset_key)
            )

        if not isinstance(partition_subset, TimeWindowPartitionsSubset):
            check.failed(f"Invalid partition subset {type(partition_subset)}")

        sorted_time_windows = sorted(partition_subset.included_time_windows)
        # no time windows, no data
        if len(sorted_time_windows) == 0:
            return None
        first_filled_time_window = sorted_time_windows[0]

        first_available_time_window = partitions_def.get_first_partition_window()
        if first_available_time_window is None:
            return None

        # if the first partition has not been filled
        if first_available_time_window.start < first_filled_time_window.start:
            return None

        # there are no events for this asset after the cursor
        asset_record = self._instance_queryer.get_asset_record(asset_key)
        if (
            asset_record is not None
            and asset_record.asset_entry is not None
            and asset_record.asset_entry.last_materialization_record is not None
            and asset_record.asset_entry.last_materialization_record.storage_id <= cursor
        ):
            return first_filled_time_window.end

        # get a per-partition count of the new materializations
        new_partition_counts = self._instance_queryer.get_materialized_partition_counts(
            asset_key, after_cursor=cursor
        )

        total_partition_counts = self._instance_queryer.get_materialized_partition_counts(asset_key)

        # these are the partitions that did not exist before this record was created
        net_new_partitions = {
            partition_key
            for partition_key, new_count in new_partition_counts.items()
            if new_count == total_partition_counts.get(partition_key)
        }

        # there are new materializations, but they don't fill any new partitions
        if not net_new_partitions:
            return first_filled_time_window.end

        # the oldest time window that was newly filled
        oldest_net_new_time_window = min(
            partitions_def.time_window_for_partition_key(partition_key)
            for partition_key in net_new_partitions
        )

        # only factor in the oldest net new time window if it breaks the current first filled time window
        return min(
            oldest_net_new_time_window.start,
            first_filled_time_window.end,
        )

    def _calculate_used_data_time_partitioned(
        self,
        asset_graph: AssetGraph,
        asset_key: AssetKey,
        cursor: int,
        partitions_def: TimeWindowPartitionsDefinition,
    ) -> Mapping[AssetKey, Tuple[Optional[int], Optional[float]]]:
        """Returns the data time (i.e. the time up to which the asset has incorporated all available
        data) for a time-partitioned asset. This method takes into account all partitions that were
        materialized for this asset up to the provided cursor.
        """
        partition_data_time = self._calculate_time_partitioned_asset_data_time(
            asset_key=asset_key,
            asset_graph=asset_graph,
            cursor=cursor,
            partitions_def=partitions_def,
        )
        partition_data_timestamp = partition_data_time.timestamp() if partition_data_time else None

        root_keys = AssetSelection.keys(asset_key).upstream().sources().resolve(asset_graph)
        return {key: (None, partition_data_timestamp) for key in root_keys}

    @cached_method
    def _calculate_used_data_unpartitioned(
        self,
        asset_graph: AssetGraph,
        asset_key: AssetKey,
        record_id: int,
        record_timestamp: Optional[float],
        record_tags: Mapping[str, str],
    ) -> Mapping[AssetKey, Tuple[Optional[int], Optional[float]]]:
        if record_id is None:
            return {key: (None, None) for key in asset_graph.get_non_source_roots(asset_key)}

        if not asset_graph.has_non_source_parents(asset_key):
            return {asset_key: (record_id, record_timestamp)}

        known_data = {}

        # find the upstream times of each of the parents of this asset
        for parent_key in asset_graph.get_parents(asset_key):
            if parent_key in asset_graph.source_asset_keys:
                continue

            input_event_pointer_tag = get_input_event_pointer_tag(parent_key)
            if input_event_pointer_tag in record_tags:
                # get the upstream materialization event which was consumed when producing this
                # materialization event
                pointer_tag = record_tags[input_event_pointer_tag]
                if pointer_tag and pointer_tag != "NULL":
                    input_record_id = int(pointer_tag)
                    parent_record = self._instance_queryer.get_latest_materialization_record(
                        parent_key, before_cursor=input_record_id + 1
                    )
                else:
                    parent_record = None
            else:
                # if the input event id was not recorded (materialized pre-1.1.0), just grab
                # the most recent asset materialization for this parent which happened before
                # the current record
                parent_record = self._instance_queryer.get_latest_materialization_record(
                    parent_key, before_cursor=record_id
                )

            # recurse to find the data times of this parent
            for key, tup in self._calculate_used_data(
                asset_graph=asset_graph,
                asset_key=parent_key,
                record_id=parent_record.storage_id if parent_record else None,
                record_timestamp=parent_record.event_log_entry.timestamp if parent_record else None,
                record_tags=frozendict(
                    (
                        parent_record.asset_materialization.tags
                        if parent_record and parent_record.asset_materialization
                        else None
                    )
                    or {}
                ),
            ).items():
                # if root data is missing, this overrides other values
                if tup == (None, None) or known_data.get(key) == (None, None):
                    known_data[key] = (None, None)
                else:
                    known_data[key] = min(known_data.get(key, tup), tup)

        return known_data

    @cached_method
    def _calculate_used_data(
        self,
        asset_graph: AssetGraph,
        asset_key: AssetKey,
        record_id: Optional[int],
        record_timestamp: Optional[float],
        record_tags: Mapping[str, str],
    ) -> Mapping[AssetKey, Tuple[Optional[int], Optional[float]]]:
        if record_id is None:
            return {key: (None, None) for key in asset_graph.get_non_source_roots(asset_key)}

        partitions_def = asset_graph.get_partitions_def(asset_key)
        if isinstance(partitions_def, TimeWindowPartitionsDefinition):
            return self._calculate_used_data_time_partitioned(
                asset_graph=asset_graph,
                asset_key=asset_key,
                cursor=record_id,
                partitions_def=partitions_def,
            )
        else:
            return self._calculate_used_data_unpartitioned(
                asset_graph=asset_graph,
                asset_key=asset_key,
                record_id=record_id,
                record_timestamp=record_timestamp,
                record_tags=record_tags,
            )

    def get_used_data_times_for_record(
        self,
        asset_graph: AssetGraph,
        record: EventLogRecord,
    ) -> Mapping[AssetKey, Optional[datetime.datetime]]:
        """Method to enable calculating the timestamps of materializations of upstream assets
        which were relevant to a given AssetMaterialization. These timestamps can be calculated relative
        to any upstream asset keys.

        The heart of this functionality is a recursive method which takes a given asset materialization
        and finds the most recent materialization of each of its parents which happened *before* that
        given materialization event.
        """
        if record.asset_key is None or record.asset_materialization is None:
            raise DagsterInvariantViolationError(
                "Can only calculate data times for records with a materialization event and an"
                " asset_key."
            )

        data = self._calculate_used_data(
            asset_graph=asset_graph,
            asset_key=record.asset_key,
            record_id=record.storage_id,
            record_timestamp=record.event_log_entry.timestamp,
            record_tags=frozendict(record.asset_materialization.tags or {}),
        )

        return {
            key: datetime.datetime.fromtimestamp(timestamp, tz=datetime.timezone.utc)
            if timestamp is not None
            else None
            for key, (_, timestamp) in data.items()
        }

    @cached_method
    def _get_in_progress_run_ids(self, current_time: datetime.datetime) -> Sequence[str]:
        return [
            record.dagster_run.run_id
            for record in self.instance.get_run_records(
                filters=RunsFilter(
                    statuses=[
                        status for status in DagsterRunStatus if status not in FINISHED_STATUSES
                    ],
                    # ignore old runs that may be stuck in an unfinished state
                    created_after=current_time - datetime.timedelta(days=1),
                ),
                limit=25,
            )
        ]

    @cached_method
    def _get_in_progress_data_times_for_key_in_run(
        self,
        run_id: str,
        current_time: datetime.datetime,
        asset_graph: AssetGraph,
        asset_key: AssetKey,
    ) -> Mapping[AssetKey, Optional[datetime.datetime]]:
        """Returns the upstream data times that a given asset key will be expected to have at the
        completion of the given run.
        """
        planned_keys = self._instance_queryer.get_planned_materializations_for_run(run_id=run_id)
        materialized_keys = self._instance_queryer.get_current_materializations_for_run(
            run_id=run_id
        )

        # if key is not pending materialization within the run, then downstream pending
        # materializations will (in general) read from the current state of the data
        if asset_key not in planned_keys or asset_key in materialized_keys:
            latest_record = self._instance_queryer.get_latest_materialization_record(asset_key)
            latest_used_data = self._calculate_used_data(
                asset_graph=asset_graph,
                asset_key=asset_key,
                record_id=latest_record.storage_id if latest_record else None,
                record_timestamp=latest_record.event_log_entry.timestamp if latest_record else None,
                record_tags=frozendict(
                    (
                        latest_record.asset_materialization.tags
                        if latest_record and latest_record.asset_materialization
                        else None
                    )
                    or {}
                ),
            )
            return {
                key: datetime.datetime.fromtimestamp(timestamp, tz=datetime.timezone.utc)
                if timestamp is not None
                else None
                for key, (_, timestamp) in latest_used_data.items()
            }

        # if you're here, then this asset is planned, but not materialized
        upstream_data_times: Dict[AssetKey, Optional[datetime.datetime]] = {}
        if not asset_graph.has_non_source_parents(asset_key):
            # in the worst case (data-time wise), this asset gets materialized right now
            upstream_data_times[asset_key] = current_time

        for parent_key in asset_graph.get_parents(asset_key):
            for upstream_key, upstream_time in self._get_in_progress_data_times_for_key_in_run(
                run_id=run_id,
                current_time=current_time,
                asset_graph=asset_graph,
                asset_key=parent_key,
            ).items():
                current_value = upstream_data_times.get(upstream_key, upstream_time)
                if current_value is None or upstream_time is None:
                    upstream_data_times[upstream_key] = None
                else:
                    upstream_data_times[upstream_key] = max(current_value, upstream_time)
        return upstream_data_times

    def get_in_progress_data_times_for_key(
        self,
        asset_graph: AssetGraph,
        asset_key: AssetKey,
        current_time: datetime.datetime,
    ) -> Mapping[AssetKey, datetime.datetime]:
        """Returns a mapping containing the maximum upstream data time that the input asset will
        have once all in-progress runs complete.
        """
        in_progress_times: Dict[AssetKey, datetime.datetime] = {}

        for run_id in self._get_in_progress_run_ids(current_time=current_time):
            if not self._instance_queryer.is_asset_planned_for_run(run_id=run_id, asset=asset_key):
                continue

            for key, time in self._get_in_progress_data_times_for_key_in_run(
                run_id=run_id,
                current_time=current_time,
                asset_graph=asset_graph,
                asset_key=asset_key,
            ).items():
                if time is not None:
                    in_progress_times[key] = max(in_progress_times.get(key, time), time)
        return in_progress_times

    def get_failed_data_times_for_key(
        self,
        asset_graph: AssetGraph,
        asset_key: AssetKey,
        upstream_keys: AbstractSet[AssetKey],
    ) -> Mapping[AssetKey, Optional[datetime.datetime]]:
        """If the latest run for this asset failed to materialize it, returns a mapping containing
        the expected data times for that asset once the run completed. Otherwise, returns an empty
        mapping.
        """
        asset_record = self._instance_queryer.get_asset_record(asset_key)

        # no latest run
        if asset_record is None or asset_record.asset_entry.last_run_id is None:
            return {}

        run_id = asset_record.asset_entry.last_run_id
        latest_run_record = self._instance_queryer._get_run_record_by_id(run_id=run_id)

        # latest run did not fail
        if (
            latest_run_record is None
            or latest_run_record.dagster_run.status != DagsterRunStatus.FAILURE
        ):
            return {}

        # run failed, but asset was materialized successfully
        latest_materialization = asset_record.asset_entry.last_materialization
        if (
            latest_materialization is not None
            and latest_materialization.run_id == latest_run_record.dagster_run.run_id
        ):
            return {}

        run_failure_time = datetime.datetime.utcfromtimestamp(
            latest_run_record.end_time or latest_run_record.create_timestamp.timestamp()
        ).replace(tzinfo=datetime.timezone.utc)
        return {
            key: min(run_failure_time, data_time) if data_time is not None else None
            for key, data_time in self._get_in_progress_data_times_for_key_in_run(
                run_id=run_id,
                current_time=run_failure_time,
                asset_graph=asset_graph,
                asset_key=asset_key,
            ).items()
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

        latest_record = self._instance_queryer.get_latest_materialization_record(asset_key)
        if latest_record is None:
            return None

        used_data_times = self.get_used_data_times_for_record(asset_graph, latest_record)

        return freshness_policy.minutes_late(
            evaluation_time=evaluation_time,
            used_data_times=used_data_times,
        )
