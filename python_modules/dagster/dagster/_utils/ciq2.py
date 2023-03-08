from collections import defaultdict
from typing import (
    Dict,
    Mapping,
    Optional,
    Sequence,
    Union,
)

from dagster._core.definitions.events import AssetKey, AssetKeyPartitionKey
from dagster._core.event_api import EventRecordsFilter
from dagster._core.events import DagsterEventType
from dagster._core.instance import DagsterInstance, DynamicPartitionsStore
from dagster._core.storage.event_log import EventLogRecord
from dagster._core.storage.event_log.base import AssetRecord
from dagster._utils.cached_method import cached_method


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

    def prefetch_asset_partition_counts(self, asset_keys: Sequence[AssetKey], after_cursor: int):
        """For performance, batches together queries for selected assets"""
        self._asset_partition_count_cache[None] = dict(
            self._instance.get_materialization_count_by_partition(
                asset_keys=asset_keys,
                after_cursor=None,
            )
        )
        self._asset_partition_count_cache[after_cursor] = dict(
            self._instance.get_materialization_count_by_partition(
                asset_keys=asset_keys,
                after_cursor=after_cursor,
            )
        )

    def prefetch_asset_records(self, asset_keys: Sequence[AssetKey]):
        """For performance, batches together queries for selected assets"""
        # get all asset records for the selected assets
        asset_records = self._instance.get_asset_records(asset_keys)
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

    def get_asset_record(self, asset_key: AssetKey) -> Optional[AssetRecord]:
        if asset_key not in self._asset_record_cache:
            self._asset_record_cache[asset_key] = next(
                iter(self._instance.get_asset_records([asset_key])), None
            )
        return self._asset_record_cache[asset_key]

    @cached_method
    def _get_latest_materialization_record(
        self,
        *,
        asset_partition: AssetKeyPartitionKey,
        before_cursor: Optional[int] = None,
    ) -> Optional[EventLogRecord]:
        records = self._instance.get_event_records(
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
    ) -> Optional[EventLogRecord]:
        if isinstance(asset, AssetKey):
            asset_partition = AssetKeyPartitionKey(asset_key=asset)
        else:
            asset_partition = asset

        # ensure we know the latest overall materialization record for this asset partition
        if asset_partition not in self._latest_materialization_record_cache:
            self._latest_materialization_record_cache[
                asset_partition
            ] = self._get_latest_materialization_record(
                asset_partition=asset_partition,
            )

        # check all of our caches to see if we can confirm that the record does not exist
        if (
            asset_partition in self._latest_materialization_record_cache
            and (
                # there is no latest record for this asset partition
                self._latest_materialization_record_cache[asset_partition] is None
                or
                # the storage id of the latest record is less than the cursor
                self._latest_materialization_record_cache[asset_partition].storage_id
                >= (after_cursor or 0)
            )
        ) or (
            # the count of this (asset key, partition key) pair is 0
            asset_partition.partition_key is not None
            and None in self._asset_partition_count_cache
            and asset_partition.asset_key in self._asset_partition_count_cache[None]
            and asset_partition.partition_key
            in self._asset_partition_count_cache[None][asset_partition.asset_key]
            and self._asset_partition_count_cache[None][asset_partition.asset_key][
                asset_partition.partition_key
            ]
            > 0
        ):
            return None

        # the latest overall record
        latest_record = self._latest_materialization_record_cache[asset_partition]

        if before_cursor is None:
            return latest_record
        else:
            if latest_record is None:
                return None
            elif latest_record.storage_id < before_cursor:
                # the latest record is before the cursor, so we can return it
                return latest_record
            else:
                # fall back to an explicit query
                return self._get_latest_materialization_record(
                    asset_partition=asset_partition, before_cursor=before_cursor
                )
