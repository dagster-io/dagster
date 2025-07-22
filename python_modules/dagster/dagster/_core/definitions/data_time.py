"""The "data time" of an asset materialization is the timestamp on its earliest ancestor
materialization.

An asset materialization is parent of another asset materialization if both:
- The child asset depends on the parent asset.
- The parent materialization is the latest materialization of the parent asset that occurred before
    the child materialization.

The idea of data time is: if an asset is downstream of another asset, then the freshness of the data
in the downstream asset depends on the freshness of the data in the upstream asset. No matter how
recently you've materialized the downstream asset, it can't be fresher than the upstream
materialization it was derived from.
"""

import datetime
from collections.abc import Mapping, Sequence
from typing import AbstractSet, Optional, cast  # noqa: UP035

from dagster_shared.utils.hash import make_hashable

import dagster._check as check
from dagster._core.definitions.asset_selection import KeysAssetSelection
from dagster._core.definitions.assets.graph.base_asset_graph import BaseAssetGraph
from dagster._core.definitions.data_version import (
    DATA_VERSION_TAG,
    DataVersion,
    get_input_event_pointer_tag,
)
from dagster._core.definitions.events import AssetKey, AssetKeyPartitionKey
from dagster._core.definitions.freshness_policy import FreshnessMinutes
from dagster._core.definitions.partitions.definition import TimeWindowPartitionsDefinition
from dagster._core.definitions.partitions.subset import TimeWindowPartitionsSubset
from dagster._core.errors import DagsterInvariantViolationError
from dagster._core.event_api import EventLogRecord
from dagster._core.storage.dagster_run import FINISHED_STATUSES, DagsterRunStatus, RunsFilter
from dagster._time import datetime_from_timestamp, get_current_datetime
from dagster._utils.cached_method import cached_method
from dagster._utils.caching_instance_queryer import CachingInstanceQueryer

DATA_TIME_METADATA_KEY = "dagster/data_time"


class CachingDataTimeResolver:
    _instance_queryer: CachingInstanceQueryer
    _asset_graph: BaseAssetGraph

    def __init__(self, instance_queryer: CachingInstanceQueryer):
        self._instance_queryer = instance_queryer

    @property
    def instance_queryer(self) -> CachingInstanceQueryer:
        return self._instance_queryer

    @property
    def asset_graph(self) -> BaseAssetGraph:
        return self.instance_queryer.asset_graph

    ####################
    # PARTITIONED DATA TIME
    ####################

    def _calculate_data_time_partitioned(
        self,
        asset_key: AssetKey,
        cursor: int,
        partitions_def: TimeWindowPartitionsDefinition,
    ) -> Optional[datetime.datetime]:
        """Returns the time up until which all available data has been consumed for this asset.

        At a high level, this algorithm works as follows:

        First, calculate the subset of partitions that have been materialized up until this point
        in time (ignoring the cursor). This is done using the get_materialized_partitions query,

        Next, we calculate the set of partitions that are net-new since the cursor. This is done by
        comparing the count of materializations before after the cursor to the total count of
        materializations.

        Finally, we calculate the minimum time window of the net-new partitions. This time window
        did not exist at the time of the cursor, so we know that we have all data up until the
        beginning of that time window, or all data up until the end of the first filled time window
        in the total set, whichever is less.
        """
        # the total set of materialized partitions
        partition_subset = partitions_def.empty_subset().with_partition_keys(
            partition_key
            for partition_key in self._instance_queryer.get_materialized_partitions(asset_key)
            if partitions_def.has_partition_key(partition_key)
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
        partitions = self._instance_queryer.get_materialized_partitions(asset_key)
        prev_partitions = self._instance_queryer.get_materialized_partitions(
            asset_key, before_cursor=cursor + 1
        )
        net_new_partitions = {
            partition_key
            for partition_key in (partitions - prev_partitions)
            if partitions_def.has_partition_key(partition_key)
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

    def _calculate_data_time_by_key_time_partitioned(
        self,
        asset_key: AssetKey,
        cursor: int,
        partitions_def: TimeWindowPartitionsDefinition,
    ) -> Mapping[AssetKey, Optional[datetime.datetime]]:
        """Returns the data time (i.e. the time up to which the asset has incorporated all available
        data) for a time-partitioned asset. This method takes into account all partitions that were
        materialized for this asset up to the provided cursor.
        """
        partition_data_time = self._calculate_data_time_partitioned(
            asset_key=asset_key,
            cursor=cursor,
            partitions_def=partitions_def,
        )

        root_keys = (
            KeysAssetSelection(selected_keys=[asset_key])
            .upstream()
            .sources()
            .resolve(self.asset_graph)
        )
        return {key: partition_data_time for key in root_keys}

    ####################
    # UNPARTITIONED DATA TIME
    ####################

    def _upstream_records_by_key(
        self, asset_key: AssetKey, record_id: int, record_tags_dict: Mapping[str, str]
    ) -> Mapping[AssetKey, "EventLogRecord"]:
        upstream_records: dict[AssetKey, EventLogRecord] = {}

        for parent_key in self.asset_graph.get(asset_key).parent_keys:
            if not (
                self.asset_graph.has(parent_key) and self.asset_graph.get(parent_key).is_executable
            ):
                continue

            input_event_pointer_tag = get_input_event_pointer_tag(parent_key)
            if input_event_pointer_tag not in record_tags_dict:
                # if the input event id was not recorded (materialized pre-1.1.0), just grab
                # the most recent event for this parent which happened before the current record
                before_cursor = record_id
            elif record_tags_dict[input_event_pointer_tag] != "NULL":
                # get the upstream event which was consumed when producing this materialization event
                before_cursor = int(record_tags_dict[input_event_pointer_tag]) + 1
            else:
                before_cursor = None

            if before_cursor is not None:
                parent_record = (
                    self._instance_queryer.get_latest_materialization_or_observation_record(
                        AssetKeyPartitionKey(parent_key), before_cursor=before_cursor
                    )
                )
                if parent_record is not None:
                    upstream_records[parent_key] = parent_record

        return upstream_records

    @cached_method
    def _calculate_data_time_by_key_unpartitioned(
        self,
        *,
        asset_key: AssetKey,
        record_id: int,
        record_timestamp: float,
        record_tags: tuple[tuple[str, str]],
        current_time: datetime.datetime,
    ) -> Mapping[AssetKey, Optional[datetime.datetime]]:
        # find the upstream times of each of the parents of this asset
        record_tags_dict = dict(record_tags)
        upstream_records_by_key = self._upstream_records_by_key(
            asset_key, record_id, record_tags_dict
        )
        if not upstream_records_by_key:
            if not self.asset_graph.has_materializable_parents(asset_key):
                return {
                    asset_key: datetime.datetime.fromtimestamp(
                        record_timestamp, tz=datetime.timezone.utc
                    )
                }
            else:
                return {}

        data_time_by_key: dict[AssetKey, Optional[datetime.datetime]] = {}
        for parent_key, parent_record in upstream_records_by_key.items():
            # recurse to find the data times of this parent
            for upstream_key, data_time in self._calculate_data_time_by_key(
                asset_key=parent_key,
                record_id=parent_record.storage_id,
                record_timestamp=parent_record.event_log_entry.timestamp,
                record_tags=make_hashable(
                    (
                        parent_record.asset_materialization.tags
                        if parent_record.asset_materialization
                        else (
                            parent_record.event_log_entry.asset_observation.tags
                            if parent_record.event_log_entry.asset_observation
                            else None
                        )
                    )
                    or {}
                ),
                current_time=current_time,
            ).items():
                # if root data is missing, this overrides other values
                if data_time is None:
                    data_time_by_key[upstream_key] = None
                else:
                    cur_data_time = data_time_by_key.get(upstream_key, data_time)
                    data_time_by_key[upstream_key] = (
                        min(cur_data_time, data_time) if cur_data_time is not None else None
                    )

        return data_time_by_key

    ####################
    # OBSERVABLE SOURCE DATA TIME
    ####################

    @cached_method
    def _calculate_data_time_by_key_observable_source(
        self,
        *,
        asset_key: AssetKey,
        record_id: int,
        record_tags: tuple[tuple[str, str]],
        current_time: datetime.datetime,
    ) -> Mapping[AssetKey, Optional[datetime.datetime]]:
        data_version_value = dict(record_tags).get(DATA_VERSION_TAG)
        if data_version_value is None:
            return {asset_key: None}

        data_version = DataVersion(data_version_value)
        next_version_record = self._instance_queryer.next_version_record(
            asset_key=asset_key, data_version=data_version, after_cursor=record_id
        )
        if next_version_record is None:
            # the most recent available version has been pulled in
            return {asset_key: current_time}

        # otherwise, we have all available data up to the point in time that the new version arrived
        next_version_timestamp = next_version_record.event_log_entry.timestamp
        return {
            asset_key: datetime.datetime.fromtimestamp(
                next_version_timestamp, tz=datetime.timezone.utc
            )
        }

    ####################
    # CORE DATA TIME
    ####################

    @cached_method
    def _calculate_data_time_by_key(
        self,
        *,
        asset_key: AssetKey,
        record_id: Optional[int],
        record_timestamp: Optional[float],
        record_tags: tuple[tuple[str, str]],  # for hashability
        current_time: datetime.datetime,
    ) -> Mapping[AssetKey, Optional[datetime.datetime]]:
        if record_id is None:
            return {key: None for key in self.asset_graph.get_materializable_roots(asset_key)}
        record_timestamp = check.not_none(record_timestamp)

        partitions_def = self.asset_graph.get(asset_key).partitions_def
        if isinstance(partitions_def, TimeWindowPartitionsDefinition):
            return self._calculate_data_time_by_key_time_partitioned(
                asset_key=asset_key,
                cursor=record_id,
                partitions_def=partitions_def,
            )
        elif self.asset_graph.get(asset_key).is_observable:
            return self._calculate_data_time_by_key_observable_source(
                asset_key=asset_key,
                record_id=record_id,
                record_tags=record_tags,
                current_time=current_time,
            )
        else:
            return self._calculate_data_time_by_key_unpartitioned(
                asset_key=asset_key,
                record_id=record_id,
                record_timestamp=record_timestamp,
                record_tags=record_tags,
                current_time=current_time,
            )

    ####################
    # IN PROGRESS DATA TIME
    ####################

    @cached_method
    def _get_in_progress_run_ids(self, current_time: datetime.datetime) -> Sequence[str]:
        return [
            record.dagster_run.run_id
            for record in self.instance_queryer.instance.get_run_records(
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
    def _get_in_progress_data_time_in_run(
        self, *, run_id: str, asset_key: AssetKey, current_time: datetime.datetime
    ) -> Optional[datetime.datetime]:
        """Returns the upstream data times that a given asset key will be expected to have at the
        completion of the given run.
        """
        planned_keys = self._instance_queryer.get_planned_materializations_for_run(run_id=run_id)
        materialized_keys = self._instance_queryer.get_current_materializations_for_run(
            run_id=run_id
        )

        # if key is not pending materialization within the run, then downstream assets will generally
        # be expected to consume the current version of the asset
        if asset_key not in planned_keys or asset_key in materialized_keys:
            return self.get_current_data_time(asset_key, current_time=current_time)

        # if you're here, then this asset is planned, but not materialized. in the worst case, this
        # asset's data time will be equal to the current time once it finishes materializing
        if not self.asset_graph.has_materializable_parents(asset_key):
            return current_time

        data_time = current_time
        for parent_key in self.asset_graph.get(asset_key).parent_keys:
            if parent_key not in self.asset_graph.materializable_asset_keys:
                continue
            parent_data_time = self._get_in_progress_data_time_in_run(
                run_id=run_id, asset_key=parent_key, current_time=current_time
            )
            if parent_data_time is None:
                return None

            data_time = min(data_time, parent_data_time)
        return data_time

    def get_in_progress_data_time(
        self, asset_key: AssetKey, current_time: datetime.datetime
    ) -> Optional[datetime.datetime]:
        """Returns a mapping containing the maximum upstream data time that the input asset will
        have once all in-progress runs complete.
        """
        data_time: Optional[datetime.datetime] = None

        for run_id in self._get_in_progress_run_ids(current_time=current_time):
            if not self._instance_queryer.is_asset_planned_for_run(run_id=run_id, asset=asset_key):
                continue

            run_data_time = self._get_in_progress_data_time_in_run(
                run_id=run_id, asset_key=asset_key, current_time=current_time
            )
            if run_data_time is not None:
                data_time = max(run_data_time, data_time or run_data_time)

        return data_time

    ####################
    # FAILED DATA TIME
    ####################

    def get_ignored_failure_data_time(
        self, asset_key: AssetKey, current_time: datetime.datetime
    ) -> Optional[datetime.datetime]:
        """Returns the data time that this asset would have if the most recent run successfully
        completed. If the most recent run did not fail, then this will return the current data time
        for this asset.
        """
        current_data_time = self.get_current_data_time(asset_key, current_time=current_time)

        asset_record = self._instance_queryer.get_asset_record(asset_key)

        # no latest run
        if asset_record is None or asset_record.asset_entry.last_run_id is None:
            return current_data_time

        run_id = asset_record.asset_entry.last_run_id
        latest_run_record = self._instance_queryer._get_run_record_by_id(  # noqa: SLF001
            run_id=run_id
        )

        # latest run did not fail
        if (
            latest_run_record is None
            or latest_run_record.dagster_run.status != DagsterRunStatus.FAILURE
        ):
            return current_data_time

        # run failed, but asset was materialized successfully
        latest_materialization = asset_record.asset_entry.last_materialization
        if (
            latest_materialization is not None
            and latest_materialization.run_id == latest_run_record.dagster_run.run_id
        ):
            return current_data_time

        run_failure_time = datetime_from_timestamp(
            latest_run_record.end_time or latest_run_record.create_timestamp.timestamp(),
        )
        return self._get_in_progress_data_time_in_run(
            run_id=run_id, asset_key=asset_key, current_time=run_failure_time
        )

    ####################
    # MAIN METHODS
    ####################

    def get_data_time_by_key_for_record(
        self,
        record: EventLogRecord,
        current_time: Optional[datetime.datetime] = None,
    ) -> Mapping[AssetKey, Optional[datetime.datetime]]:
        """Method to enable calculating the timestamps of materializations or observations of
        upstream assets which were relevant to a given AssetMaterialization. These timestamps can
        be calculated relative to any upstream asset keys.

        The heart of this functionality is a recursive method which takes a given asset materialization
        and finds the most recent materialization of each of its parents which happened *before* that
        given materialization event.
        """
        event = record.asset_materialization or record.asset_observation
        if record.asset_key is None or event is None:
            raise DagsterInvariantViolationError(
                "Can only calculate data times for records with a materialization / observation "
                "event and an asset_key."
            )

        return self._calculate_data_time_by_key(
            asset_key=record.asset_key,
            record_id=record.storage_id,
            record_timestamp=record.event_log_entry.timestamp,
            record_tags=make_hashable(event.tags or {}),
            current_time=current_time or get_current_datetime(),
        )

    def get_current_data_time(
        self, asset_key: AssetKey, current_time: datetime.datetime
    ) -> Optional[datetime.datetime]:
        latest_record = self.instance_queryer.get_latest_materialization_or_observation_record(
            AssetKeyPartitionKey(asset_key)
        )
        if latest_record is None:
            return None

        data_times = set(self.get_data_time_by_key_for_record(latest_record, current_time).values())

        if None in data_times or not data_times:
            return None

        return min(cast("AbstractSet[datetime.datetime]", data_times), default=None)

    def _get_source_data_time(
        self, asset_key: AssetKey, current_time: datetime.datetime
    ) -> Optional[datetime.datetime]:
        latest_record = self.instance_queryer.get_latest_materialization_or_observation_record(
            AssetKeyPartitionKey(asset_key)
        )
        if latest_record is None:
            return None
        observation = latest_record.asset_observation
        if observation is None:
            check.failed(
                "when invoked on a source asset, "
                "get_latest_materialization_or_observation_record should always return an "
                "observation"
            )

        data_time = observation.metadata.get(DATA_TIME_METADATA_KEY)
        if data_time is None:
            return None
        else:
            return datetime.datetime.fromtimestamp(
                cast("float", data_time.value), datetime.timezone.utc
            )

    def get_minutes_overdue(
        self,
        asset_key: AssetKey,
        evaluation_time: datetime.datetime,
    ) -> Optional[FreshnessMinutes]:
        asset = self.asset_graph.get(asset_key)
        if asset.legacy_freshness_policy is None:
            raise DagsterInvariantViolationError(
                "Cannot calculate minutes late for asset without a FreshnessPolicy"
            )

        if asset.is_observable:
            current_data_time = self._get_source_data_time(asset_key, current_time=evaluation_time)
        else:
            current_data_time = self.get_current_data_time(asset_key, current_time=evaluation_time)

        return asset.legacy_freshness_policy.minutes_overdue(
            data_time=current_data_time,
            evaluation_time=evaluation_time,
        )
