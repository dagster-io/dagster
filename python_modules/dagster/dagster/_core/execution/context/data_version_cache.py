import os
from typing import TYPE_CHECKING

"""This module contains the execution context objects that are internal to the system.
Not every property on these should be exposed to random Jane or Joe dagster user
so we have a different layer of objects that encode the explicit public API
in the user_context module.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from hashlib import sha256
from typing import Optional

import dagster._check as check
from dagster._core.definitions.data_version import (
    DATA_VERSION_TAG,
    SKIP_PARTITION_DATA_VERSION_DEPENDENCY_THRESHOLD,
    extract_data_version_from_entry,
)
from dagster._core.definitions.events import AssetKey

if TYPE_CHECKING:
    from dagster._core.definitions.data_version import DataVersion
    from dagster._core.event_api import EventLogRecord
    from dagster._core.events import DagsterEventType
    from dagster._core.storage.event_log.base import AssetRecord


if TYPE_CHECKING:
    from dagster._core.execution.context.compute import StepExecutionContext


@dataclass
class InputAssetVersionInfo:
    # This is the storage id of the last materialization/observation of any partition of an asset.
    # Thus it is computed the same way for both partitioned and non-partitioned assets.
    storage_id: int

    # This is the event type of the event referenced by storage_id
    event_type: "DagsterEventType"

    # If the input asset is partitioned, this is a hash of the sorted data versions of each dependency
    # partition. If the input asset is not partitioned, this is the data version of the asset. It
    # can be none if we are sourcing a materialization from before data versions.
    data_version: Optional["DataVersion"]

    # This is the run_id on the event that the storage_id references
    run_id: str

    # This is the timestamp on the event that the storage_id references
    timestamp: float


class DataVersionCache:
    def __init__(self, context: "StepExecutionContext"):
        self._context = context
        self.input_asset_version_info: dict[AssetKey, Optional[InputAssetVersionInfo]] = {}
        self.is_external_input_asset_version_info_loaded = False
        self.values: dict[AssetKey, DataVersion] = {}

    def set_data_version(self, asset_key: AssetKey, data_version: "DataVersion") -> None:
        self.values[asset_key] = data_version

    def has_data_version(self, asset_key: AssetKey) -> bool:
        return asset_key in self.values

    def get_data_version(self, asset_key: AssetKey) -> "DataVersion":
        return self.values[asset_key]

    def maybe_fetch_and_get_input_asset_version_info(
        self, key: AssetKey
    ) -> Optional["InputAssetVersionInfo"]:
        if key not in self.input_asset_version_info:
            self._fetch_input_asset_version_info([key])
        return self.input_asset_version_info[key]

    # "external" refers to records for inputs generated outside of this step
    def fetch_external_input_asset_version_info(self) -> None:
        output_keys = self._context.get_output_asset_keys()

        all_dep_keys: list[AssetKey] = []
        for output_key in output_keys:
            if not self._context.job_def.asset_layer.has(output_key):
                continue
            dep_keys = self._context.job_def.asset_layer.get(output_key).parent_keys
            for key in dep_keys:
                if key not in all_dep_keys and key not in output_keys:
                    all_dep_keys.append(key)

        self.input_asset_version_info = {}
        self._fetch_input_asset_version_info(all_dep_keys)
        self.is_external_input_asset_version_info_loaded = True

    def _fetch_input_asset_version_info(self, asset_keys: Sequence[AssetKey]) -> None:
        from dagster._core.definitions.data_version import extract_data_version_from_entry

        asset_records_by_key = self._fetch_asset_records(asset_keys)
        for key in asset_keys:
            asset_record = asset_records_by_key.get(key)
            event = self._get_input_asset_event(key, asset_record)
            if event is None:
                self.input_asset_version_info[key] = None
            else:
                storage_id = event.storage_id
                # Input name will be none if this is an internal dep
                input_name = self._context.job_def.asset_layer.get_node_input_name(
                    self._context.node_handle, key
                )
                # Exclude AllPartitionMapping for now to avoid huge queries
                if input_name and self._context.has_asset_partitions_for_input(input_name):
                    subset = self._context.asset_partitions_subset_for_input(
                        input_name, require_valid_partitions=False
                    )
                    input_keys = list(subset.get_partition_keys())

                    # This check represents a temporary constraint that prevents huge query results for upstream
                    # partition data versions from timing out runs. If a partitioned dependency (a) uses an
                    # AllPartitionMapping; and (b) has greater than or equal to
                    # SKIP_PARTITION_DATA_VERSION_DEPENDENCY_THRESHOLD dependency partitions, then we
                    # process it as a non-partitioned dependency (note that this was the behavior for
                    # all partition dependencies prior to 2023-08).  This means that stale status
                    # results cannot be accurately computed for the dependency, and there is thus
                    # corresponding logic in the CachingStaleStatusResolver to account for this. This
                    # constraint should be removed when we have thoroughly examined the performance of
                    # the data version retrieval query and can guarantee decent performance.
                    if len(input_keys) < SKIP_PARTITION_DATA_VERSION_DEPENDENCY_THRESHOLD:
                        data_version = self._get_partitions_data_version_from_keys(key, input_keys)
                    else:
                        data_version = extract_data_version_from_entry(event.event_log_entry)
                else:
                    data_version = extract_data_version_from_entry(event.event_log_entry)
                self.input_asset_version_info[key] = InputAssetVersionInfo(
                    storage_id,
                    check.not_none(event.event_log_entry.dagster_event).event_type,
                    data_version,
                    event.run_id,
                    event.timestamp,
                )

    def _fetch_asset_records(self, asset_keys: Sequence[AssetKey]) -> dict[AssetKey, "AssetRecord"]:
        batch_size = int(os.getenv("GET_ASSET_RECORDS_FOR_DATA_VERSION_BATCH_SIZE", "100"))
        asset_records_by_key = {}
        to_fetch = asset_keys
        while len(to_fetch):
            for record in self._context.instance.get_asset_records(to_fetch[:batch_size]):
                asset_records_by_key[record.asset_entry.asset_key] = record
            to_fetch = to_fetch[batch_size:]

        return asset_records_by_key

    def _get_input_asset_event(
        self, key: AssetKey, asset_record: Optional["AssetRecord"]
    ) -> Optional["EventLogRecord"]:
        event = None
        if asset_record and asset_record.asset_entry.last_materialization_record:
            event = asset_record.asset_entry.last_materialization_record
        elif (
            asset_record
            and self._context.instance.event_log_storage.asset_records_have_last_observation
        ):
            event = asset_record.asset_entry.last_observation_record

        if (
            not event
            and not self._context.instance.event_log_storage.asset_records_have_last_observation
        ):
            event = next(
                iter(self._context.instance.fetch_observations(key, limit=1).records), None
            )

        if event:
            self._check_input_asset_event(key, event)
        return event

    def _check_input_asset_event(self, key: AssetKey, event: "EventLogRecord") -> None:
        assert event.event_log_entry
        event_data_version = extract_data_version_from_entry(event.event_log_entry)
        if key in self.values and self.values[key] != event_data_version:
            self._context.log.warning(
                f"Data version mismatch for asset {key}. Data version from materialization within"
                f" current step is `{self.values[key]}`. Data version from most recent"
                f" materialization is `{event_data_version}`. Most recent materialization will be"
                " used for provenance tracking."
            )

    def _get_partitions_data_version_from_keys(
        self, key: AssetKey, partition_keys: Sequence[str]
    ) -> "DataVersion":
        from dagster._core.definitions.data_version import DataVersion
        from dagster._core.events import DagsterEventType

        # TODO: this needs to account for observations also
        event_type = DagsterEventType.ASSET_MATERIALIZATION
        tags_by_partition = self._context.instance._event_storage.get_latest_tags_by_partition(  # noqa: SLF001
            key, event_type, [DATA_VERSION_TAG], asset_partitions=list(partition_keys)
        )
        partition_data_versions = [
            pair[1][DATA_VERSION_TAG]
            for pair in sorted(tags_by_partition.items(), key=lambda x: x[0])
        ]
        hash_sig = sha256()
        hash_sig.update(bytearray("".join(partition_data_versions), "utf8"))
        return DataVersion(hash_sig.hexdigest())

    # Call this to clear the cache for an input asset record. This is necessary when an old
    # materialization for an asset was loaded during `fetch_external_input_asset_records` because an
    # intrastep asset is not required, but then that asset is materialized during the step. If we
    # don't clear the cache for this asset, then we won't use the most up-to-date asset record.
    def wipe_input_asset_version_info(self, key: AssetKey) -> None:
        if key in self.input_asset_version_info:
            del self.input_asset_version_info[key]
