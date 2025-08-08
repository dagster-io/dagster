import os
from collections.abc import Iterable, Mapping, Sequence
from typing import TYPE_CHECKING, Optional, Union, cast

from dagster._annotations import deprecated, public
from dagster._utils import traced

if TYPE_CHECKING:
    from dagster._core.definitions.asset_checks.asset_check_evaluation import AssetCheckEvaluation
    from dagster._core.definitions.asset_checks.asset_check_spec import AssetCheckKey
    from dagster._core.definitions.asset_health.asset_check_health import AssetCheckHealthState
    from dagster._core.definitions.asset_health.asset_freshness_health import (
        AssetFreshnessHealthState,
    )
    from dagster._core.definitions.asset_health.asset_materialization_health import (
        AssetMaterializationHealthState,
        MinimalAssetMaterializationHealthState,
    )
    from dagster._core.definitions.events import AssetKey, AssetObservation
    from dagster._core.definitions.freshness import (
        FreshnessStateChange,
        FreshnessStateEvaluation,
        FreshnessStateRecord,
    )
    from dagster._core.definitions.partitions.definition import PartitionsDefinition
    from dagster._core.event_api import AssetRecordsFilter
    from dagster._core.events import AssetMaterialization
    from dagster._core.events.log import EventLogEntry
    from dagster._core.instance.assets.asset_domain import AssetDomain
    from dagster._core.storage.asset_check_execution_record import (
        AssetCheckExecutionRecord,
        AssetCheckInstanceSupport,
    )
    from dagster._core.storage.event_log import EventLogStorage
    from dagster._core.storage.event_log.base import (
        AssetRecord,
        EventLogRecord,
        EventRecordsResult,
        PlannedMaterializationInfo,
    )
    from dagster._core.storage.partition_status_cache import (
        AssetPartitionStatus,
        AssetStatusCacheValue,
    )


class AssetMixin:
    """Mixin providing asset-related methods for DagsterInstance."""

    @property
    def _asset_domain(self) -> "AssetDomain":
        """Access the asset domain. This will be available when mixed with DomainsMixin."""
        return cast("AssetDomain", getattr(self, "asset_domain"))

    @property
    def _event_log_storage(self) -> "EventLogStorage":
        """Access the event log storage."""
        return cast("EventLogStorage", getattr(self, "_event_storage"))

    @property
    def _event_log_storage_prop(self) -> "EventLogStorage":
        """Access the event log storage via event_log_storage property."""
        return cast("EventLogStorage", getattr(self, "event_log_storage"))

    # asset storage

    @traced
    def can_read_asset_status_cache(self) -> bool:
        return self._asset_domain.can_read_asset_status_cache()

    @traced
    def update_asset_cached_status_data(
        self, asset_key: "AssetKey", cache_values: "AssetStatusCacheValue"
    ) -> None:
        self._asset_domain.update_asset_cached_status_data(asset_key, cache_values)

    @traced
    def wipe_asset_cached_status(self, asset_keys: Sequence["AssetKey"]) -> None:
        self._asset_domain.wipe_asset_cached_status(asset_keys)

    @traced
    def all_asset_keys(self) -> Sequence["AssetKey"]:
        return self._asset_domain.all_asset_keys()

    @public
    @traced
    def get_asset_keys(
        self,
        prefix: Optional[Sequence[str]] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> Sequence["AssetKey"]:
        """Return a filtered subset of asset keys managed by this instance.

        Args:
            prefix (Optional[Sequence[str]]): Return only assets having this key prefix.
            limit (Optional[int]): Maximum number of keys to return.
            cursor (Optional[str]): Cursor to use for pagination.

        Returns:
            Sequence[AssetKey]: List of asset keys.
        """
        return self._asset_domain.get_asset_keys(prefix, limit, cursor)

    @public
    @traced
    def has_asset_key(self, asset_key: "AssetKey") -> bool:
        """Return true if this instance manages the given asset key.

        Args:
            asset_key (AssetKey): Asset key to check.
        """
        return self._asset_domain.has_asset_key(asset_key)

    @traced
    def get_latest_materialization_events(
        self, asset_keys: Iterable["AssetKey"]
    ) -> Mapping["AssetKey", Optional["EventLogEntry"]]:
        return self._asset_domain.get_latest_materialization_events(asset_keys)

    @public
    @traced
    def get_latest_materialization_event(self, asset_key: "AssetKey") -> Optional["EventLogEntry"]:
        """Fetch the latest materialization event for the given asset key.

        Args:
            asset_key (AssetKey): Asset key to return materialization for.

        Returns:
            Optional[EventLogEntry]: The latest materialization event for the given asset
                key, or `None` if the asset has not been materialized.
        """
        return self._asset_domain.get_latest_materialization_event(asset_key)

    @traced
    def get_latest_asset_check_evaluation_record(
        self, asset_check_key: "AssetCheckKey"
    ) -> Optional["AssetCheckExecutionRecord"]:
        return self._asset_domain.get_latest_asset_check_evaluation_record(asset_check_key)

    @public
    @traced
    def fetch_materializations(
        self,
        records_filter: Union["AssetKey", "AssetRecordsFilter"],
        limit: int,
        cursor: Optional[str] = None,
        ascending: bool = False,
    ) -> "EventRecordsResult":
        """Return a list of materialization records stored in the event log storage.

        Args:
            records_filter (Union[AssetKey, AssetRecordsFilter]): the filter by which to
                filter event records.
            limit (int): Number of results to get.
            cursor (Optional[str]): Cursor to use for pagination. Defaults to None.
            ascending (Optional[bool]): Sort the result in ascending order if True, descending
                otherwise. Defaults to descending.

        Returns:
            EventRecordsResult: Object containing a list of event log records and a cursor string
        """
        return self._asset_domain.fetch_materializations(records_filter, limit, cursor, ascending)

    @traced
    def fetch_failed_materializations(
        self,
        records_filter: Union["AssetKey", "AssetRecordsFilter"],
        limit: int,
        cursor: Optional[str] = None,
        ascending: bool = False,
    ) -> "EventRecordsResult":
        """Return a list of AssetFailedToMaterialization records stored in the event log storage.

        Args:
            records_filter (Union[AssetKey, AssetRecordsFilter]): the filter by which to
                filter event records.
            limit (int): Number of results to get.
            cursor (Optional[str]): Cursor to use for pagination. Defaults to None.
            ascending (Optional[bool]): Sort the result in ascending order if True, descending
                otherwise. Defaults to descending.

        Returns:
            EventRecordsResult: Object containing a list of event log records and a cursor string
        """
        return self._asset_domain.fetch_failed_materializations(
            records_filter, limit, cursor, ascending
        )

    @traced
    @deprecated(breaking_version="2.0")
    def fetch_planned_materializations(
        self,
        records_filter: Union["AssetKey", "AssetRecordsFilter"],
        limit: int,
        cursor: Optional[str] = None,
        ascending: bool = False,
    ) -> "EventRecordsResult":
        """Return a list of planned materialization records stored in the event log storage.

        Args:
            records_filter (Optional[Union[AssetKey, AssetRecordsFilter]]): the filter by which to
                filter event records.
            limit (int): Number of results to get.
            cursor (Optional[str]): Cursor to use for pagination. Defaults to None.
            ascending (Optional[bool]): Sort the result in ascending order if True, descending
                otherwise. Defaults to descending.

        Returns:
            EventRecordsResult: Object containing a list of event log records and a cursor string
        """
        return self._asset_domain.fetch_planned_materializations(
            records_filter, limit, cursor, ascending
        )

    @public
    @traced
    def fetch_observations(
        self,
        records_filter: Union["AssetKey", "AssetRecordsFilter"],
        limit: int,
        cursor: Optional[str] = None,
        ascending: bool = False,
    ) -> "EventRecordsResult":
        """Return a list of observation records stored in the event log storage.

        Args:
            records_filter (Optional[Union[AssetKey, AssetRecordsFilter]]): the filter by which to
                filter event records.
            limit (int): Number of results to get.
            cursor (Optional[str]): Cursor to use for pagination. Defaults to None.
            ascending (Optional[bool]): Sort the result in ascending order if True, descending
                otherwise. Defaults to descending.

        Returns:
            EventRecordsResult: Object containing a list of event log records and a cursor string
        """
        return self._event_log_storage.fetch_observations(records_filter, limit, cursor, ascending)

    @public
    @traced
    def get_status_by_partition(
        self,
        asset_key: "AssetKey",
        partition_keys: Sequence[str],
        partitions_def: "PartitionsDefinition",
    ) -> Optional[Mapping[str, "AssetPartitionStatus"]]:
        """Get the current status of provided partition_keys for the provided asset.

        Args:
            asset_key (AssetKey): The asset to get per-partition status for.
            partition_keys (Sequence[str]): The partitions to get status for.
            partitions_def (PartitionsDefinition): The PartitionsDefinition of the asset to get
                per-partition status for.

        Returns:
            Optional[Mapping[str, AssetPartitionStatus]]: status for each partition key

        """
        return self._asset_domain.get_status_by_partition(asset_key, partition_keys, partitions_def)

    @public
    @traced
    def get_asset_records(
        self, asset_keys: Optional[Sequence["AssetKey"]] = None
    ) -> Sequence["AssetRecord"]:
        """Return an `AssetRecord` for each of the given asset keys.

        Args:
            asset_keys (Optional[Sequence[AssetKey]]): List of asset keys to retrieve records for.

        Returns:
            Sequence[AssetRecord]: List of asset records.
        """
        return self._asset_domain.get_asset_records(asset_keys)

    @traced
    def get_event_tags_for_asset(
        self,
        asset_key: "AssetKey",
        filter_tags: Optional[Mapping[str, str]] = None,
        filter_event_id: Optional[int] = None,
    ) -> Sequence[Mapping[str, str]]:
        """Fetches asset event tags for the given asset key.

        If filter_tags is provided, searches for events containing all of the filter tags. Then,
        returns all tags for those events. This enables searching for multipartitioned asset
        partition tags with a fixed dimension value, e.g. all of the tags for events where
        "country" == "US".

        If filter_event_id is provided, searches for the event with the provided event_id.

        Returns a list of dicts, where each dict is a mapping of tag key to tag value for a
        single event.
        """
        return self._asset_domain.get_event_tags_for_asset(asset_key, filter_tags, filter_event_id)

    @public
    @traced
    def wipe_assets(self, asset_keys: Sequence["AssetKey"]) -> None:
        """Wipes asset event history from the event log for the given asset keys.

        Args:
            asset_keys (Sequence[AssetKey]): Asset keys to wipe.
        """
        self._asset_domain.wipe_assets(asset_keys)

    def wipe_asset_partitions(
        self,
        asset_key: "AssetKey",
        partition_keys: Sequence[str],
    ) -> None:
        """Wipes asset event history from the event log for the given asset key and partition keys.

        Args:
            asset_key (AssetKey): Asset key to wipe.
            partition_keys (Sequence[str]): Partition keys to wipe.
        """
        self._asset_domain.wipe_asset_partitions(asset_key, partition_keys)

    @traced
    def get_materialized_partitions(
        self,
        asset_key: "AssetKey",
        before_cursor: Optional[int] = None,
        after_cursor: Optional[int] = None,
    ) -> set[str]:
        return self._asset_domain.get_materialized_partitions(
            asset_key, before_cursor, after_cursor
        )

    @traced
    def get_latest_planned_materialization_info(
        self,
        asset_key: "AssetKey",
        partition: Optional[str] = None,
    ) -> Optional["PlannedMaterializationInfo"]:
        return self._asset_domain.get_latest_planned_materialization_info(asset_key, partition)

    def get_latest_data_version_record(
        self,
        key: "AssetKey",
        is_source: Optional[bool] = None,
        partition_key: Optional[str] = None,
        before_cursor: Optional[int] = None,
        after_cursor: Optional[int] = None,
    ) -> Optional["EventLogRecord"]:
        return self._asset_domain.get_latest_data_version_record(
            key, is_source, partition_key, before_cursor, after_cursor
        )

    @public
    def get_latest_materialization_code_versions(
        self, asset_keys: Iterable["AssetKey"]
    ) -> Mapping["AssetKey", Optional[str]]:
        """Returns the code version used for the latest materialization of each of the provided
        assets.

        Args:
            asset_keys (Iterable[AssetKey]): The asset keys to find latest materialization code
                versions for.

        Returns:
            Mapping[AssetKey, Optional[str]]: A dictionary with a key for each of the provided asset
                keys. The values will be None if the asset has no materializations. If an asset does
                not have a code version explicitly assigned to its definitions, but was
                materialized, Dagster assigns the run ID as its code version.
        """
        return self._asset_domain.get_latest_materialization_code_versions(asset_keys)

    @public
    def report_runless_asset_event(
        self,
        asset_event: Union[
            "AssetMaterialization",
            "AssetObservation",
            "AssetCheckEvaluation",
            "FreshnessStateEvaluation",
            "FreshnessStateChange",
        ],
    ):
        """Record an event log entry related to assets that does not belong to a Dagster run."""
        return self._asset_domain.report_runless_asset_event(asset_event)

    def _report_runless_asset_event(
        self,
        asset_event: Union[
            "AssetMaterialization",
            "AssetObservation",
            "AssetCheckEvaluation",
            "FreshnessStateEvaluation",
            "FreshnessStateChange",
        ],
    ):
        """Use this directly over report_runless_asset_event to emit internal events."""
        return self._asset_domain._report_runless_asset_event(asset_event)  # noqa: SLF001

    def get_asset_check_health_state_for_assets(
        self, _asset_keys: Sequence["AssetKey"]
    ) -> Optional[Mapping["AssetKey", Optional["AssetCheckHealthState"]]]:
        return self._asset_domain.get_asset_check_health_state_for_assets(_asset_keys)

    def get_asset_freshness_health_state_for_assets(
        self, _asset_keys: Sequence["AssetKey"]
    ) -> Optional[Mapping["AssetKey", Optional["AssetFreshnessHealthState"]]]:
        return self._asset_domain.get_asset_freshness_health_state_for_assets(_asset_keys)

    def get_asset_materialization_health_state_for_assets(
        self, _asset_keys: Sequence["AssetKey"]
    ) -> Optional[Mapping["AssetKey", Optional["AssetMaterializationHealthState"]]]:
        return self._asset_domain.get_asset_materialization_health_state_for_assets(_asset_keys)

    def get_minimal_asset_materialization_health_state_for_assets(
        self, asset_keys: Sequence["AssetKey"]
    ) -> Optional[Mapping["AssetKey", Optional["MinimalAssetMaterializationHealthState"]]]:
        return self._asset_domain.get_minimal_asset_materialization_health_state_for_assets(
            asset_keys
        )

    def get_freshness_state_records(
        self, keys: Sequence["AssetKey"]
    ) -> Mapping["AssetKey", "FreshnessStateRecord"]:
        return self._event_log_storage.get_freshness_state_records(keys)

    def get_asset_check_support(self) -> "AssetCheckInstanceSupport":
        from dagster._core.storage.asset_check_execution_record import AssetCheckInstanceSupport

        return (
            AssetCheckInstanceSupport.SUPPORTED
            if self._event_log_storage_prop.supports_asset_checks
            else AssetCheckInstanceSupport.NEEDS_MIGRATION
        )

    def dagster_asset_health_queries_supported(self) -> bool:
        return False

    def can_read_failure_events_for_asset(self, _asset_record: "AssetRecord") -> bool:
        return False

    def can_read_asset_failure_events(self) -> bool:
        return False

    def internal_asset_freshness_enabled(self) -> bool:
        return os.getenv("DAGSTER_ASSET_FRESHNESS_ENABLED", "").lower() == "true"

    def streamline_read_asset_health_supported(self) -> bool:
        return False

    def streamline_read_asset_health_required(self) -> bool:
        return False
