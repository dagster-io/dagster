import os
from collections.abc import Iterable, Mapping, Sequence
from typing import TYPE_CHECKING, Optional, Union, cast

from dagster._annotations import deprecated
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
    from dagster._core.storage.partition_status_cache import AssetStatusCacheValue


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

    @traced
    def get_latest_materialization_events(
        self, asset_keys: Iterable["AssetKey"]
    ) -> Mapping["AssetKey", Optional["EventLogEntry"]]:
        return self._asset_domain.get_latest_materialization_events(asset_keys)

    @traced
    def get_latest_asset_check_evaluation_record(
        self, asset_check_key: "AssetCheckKey"
    ) -> Optional["AssetCheckExecutionRecord"]:
        return self._asset_domain.get_latest_asset_check_evaluation_record(asset_check_key)

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
