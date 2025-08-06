"""Asset domain implementation - extracted from DagsterInstance."""

from collections.abc import Iterable, Mapping, Sequence
from typing import TYPE_CHECKING, Optional, Union

import dagster._check as check
from dagster._core.definitions.asset_checks.asset_check_evaluation import AssetCheckEvaluation
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.events import AssetObservation
from dagster._core.definitions.freshness import FreshnessStateChange, FreshnessStateEvaluation

if TYPE_CHECKING:
    from dagster._core.definitions.asset_health.asset_check_health import AssetCheckHealthState
    from dagster._core.definitions.asset_health.asset_freshness_health import (
        AssetFreshnessHealthState,
    )
    from dagster._core.definitions.asset_health.asset_materialization_health import (
        AssetMaterializationHealthState,
        MinimalAssetMaterializationHealthState,
    )
    from dagster._core.definitions.asset_key import AssetCheckKey
    from dagster._core.definitions.events import AssetMaterialization
    from dagster._core.event_api import EventRecordsResult
    from dagster._core.events import DagsterEventType
    from dagster._core.events.log import EventLogEntry
    from dagster._core.instance import DagsterInstance
    from dagster._core.storage.asset_check_execution_record import AssetCheckExecutionRecord
    from dagster._core.storage.event_log.base import (
        AssetRecord,
        AssetRecordsFilter,
        PlannedMaterializationInfo,
    )
    from dagster._core.storage.partition_status_cache import AssetStatusCacheValue


class AssetDomain:
    """Domain object encapsulating asset-related operations.

    This class holds a reference to a DagsterInstance and provides methods
    for asset management, materialization tracking, and health monitoring.
    """

    def __init__(self, instance: "DagsterInstance") -> None:
        self._instance = instance

    def can_read_asset_status_cache(self) -> bool:
        """Check if asset status cache can be read - moved from DagsterInstance.can_read_asset_status_cache()."""
        return self._instance._event_storage.can_read_asset_status_cache()  # noqa: SLF001

    def update_asset_cached_status_data(
        self, asset_key: "AssetKey", cache_values: "AssetStatusCacheValue"
    ) -> None:
        """Update asset cached status data - moved from DagsterInstance.update_asset_cached_status_data()."""
        self._instance._event_storage.update_asset_cached_status_data(asset_key, cache_values)  # noqa: SLF001

    def wipe_asset_cached_status(self, asset_keys: Sequence["AssetKey"]) -> None:
        """Wipe asset cached status - moved from DagsterInstance.wipe_asset_cached_status()."""
        from dagster._core.definitions.asset_key import AssetKey

        check.list_param(asset_keys, "asset_keys", of_type=AssetKey)
        for asset_key in asset_keys:
            self._instance._event_storage.wipe_asset_cached_status(asset_key)  # noqa: SLF001

    def all_asset_keys(self) -> Sequence["AssetKey"]:
        """Get all asset keys - moved from DagsterInstance.all_asset_keys()."""
        return self._instance._event_storage.all_asset_keys()  # noqa: SLF001

    def get_asset_keys(
        self,
        prefix: Optional[Sequence[str]] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> Sequence["AssetKey"]:
        """Return a filtered subset of asset keys managed by this instance.
        Moved from DagsterInstance.get_asset_keys().

        Args:
            prefix (Optional[Sequence[str]]): Return only assets having this key prefix.
            limit (Optional[int]): Maximum number of keys to return.
            cursor (Optional[str]): Cursor to use for pagination.

        Returns:
            Sequence[AssetKey]: List of asset keys.
        """
        return self._instance._event_storage.get_asset_keys(  # noqa: SLF001
            prefix=prefix, limit=limit, cursor=cursor
        )

    def has_asset_key(self, asset_key: "AssetKey") -> bool:
        """Return true if this instance manages the given asset key.
        Moved from DagsterInstance.has_asset_key().

        Args:
            asset_key (AssetKey): Asset key to check.
        """
        return self._instance._event_storage.has_asset_key(asset_key)  # noqa: SLF001

    def get_latest_materialization_events(
        self, asset_keys: Iterable["AssetKey"]
    ) -> Mapping["AssetKey", Optional["EventLogEntry"]]:
        """Get latest materialization events - moved from DagsterInstance.get_latest_materialization_events()."""
        return self._instance._event_storage.get_latest_materialization_events(asset_keys)  # noqa: SLF001

    def get_latest_materialization_event(self, asset_key: "AssetKey") -> Optional["EventLogEntry"]:
        """Fetch the latest materialization event for the given asset key.
        Moved from DagsterInstance.get_latest_materialization_event().

        Args:
            asset_key (AssetKey): Asset key to return materialization for.

        Returns:
            Optional[EventLogEntry]: The latest materialization event for the given asset
                key, or `None` if the asset has not been materialized.
        """
        return self._instance._event_storage.get_latest_materialization_events([asset_key]).get(  # noqa: SLF001
            asset_key
        )

    def get_latest_asset_check_evaluation_record(
        self, asset_check_key: "AssetCheckKey"
    ) -> Optional["AssetCheckExecutionRecord"]:
        """Get latest asset check evaluation record - moved from DagsterInstance.get_latest_asset_check_evaluation_record()."""
        return self._instance._event_storage.get_latest_asset_check_execution_by_key(  # noqa: SLF001
            [asset_check_key]
        ).get(asset_check_key)

    def fetch_materializations(
        self,
        records_filter: Union["AssetKey", "AssetRecordsFilter"],
        limit: int,
        cursor: Optional[str] = None,
        ascending: bool = False,
    ) -> "EventRecordsResult":
        """Return a list of materialization records stored in the event log storage.
        Moved from DagsterInstance.fetch_materializations().

        Args:
            records_filter (Union[AssetKey, AssetRecordsFilter]): the filter by which to
                filter event records.
            limit (int): Number of results to get.
            cursor (Optional[str]): Cursor to use for pagination. Defaults to None.
            ascending (Optional[bool]): Sort the result in ascending order if True, descending
                otherwise. Defaults to descending.

        Returns:
            EventRecordsResult: Object containing a list of event log records and a cursor string.
        """
        return self._instance._event_storage.fetch_materializations(  # noqa: SLF001
            records_filter, limit, cursor, ascending
        )

    def fetch_failed_materializations(
        self,
        records_filter: Union["AssetKey", "AssetRecordsFilter"],
        limit: int,
        cursor: Optional[str] = None,
        ascending: bool = False,
    ) -> "EventRecordsResult":
        """Return a list of AssetFailedToMaterialization records stored in the event log storage.
        Moved from DagsterInstance.fetch_failed_materializations().

        Args:
            records_filter (Union[AssetKey, AssetRecordsFilter]): the filter by which to
                filter event records.
            limit (int): Number of results to get.
            cursor (Optional[str]): Cursor to use for pagination. Defaults to None.
            ascending (Optional[bool]): Sort the result in ascending order if True, descending
                otherwise. Defaults to descending.

        Returns:
            EventRecordsResult: Object containing a list of event log records and a cursor string.
        """
        return self._instance._event_storage.fetch_failed_materializations(  # noqa: SLF001
            records_filter, limit, cursor, ascending
        )

    def wipe_assets(self, asset_keys: Sequence["AssetKey"]) -> None:
        """Wipes asset event history from the event log for the given asset keys.
        Moved from DagsterInstance.wipe_assets().

        Args:
            asset_keys (Sequence[AssetKey]): Asset keys to wipe.
        """
        from dagster._core.definitions.asset_key import AssetKey
        from dagster._core.events import AssetWipedData, DagsterEvent, DagsterEventType
        from dagster._core.instance.utils import RUNLESS_JOB_NAME, RUNLESS_RUN_ID

        check.list_param(asset_keys, "asset_keys", of_type=AssetKey)
        for asset_key in asset_keys:
            self._instance._event_storage.wipe_asset(asset_key)  # noqa: SLF001
            self._instance.report_dagster_event(
                DagsterEvent(
                    event_type_value=DagsterEventType.ASSET_WIPED.value,
                    event_specific_data=AssetWipedData(asset_key=asset_key, partition_keys=None),
                    job_name=RUNLESS_JOB_NAME,
                ),
                run_id=RUNLESS_RUN_ID,
            )

    def wipe_asset_partitions(
        self,
        asset_key: "AssetKey",
        partition_keys: Sequence[str],
    ) -> None:
        """Wipes asset event history from the event log for the given asset key and partition keys.
        Moved from DagsterInstance.wipe_asset_partitions().

        Args:
            asset_key (AssetKey): Asset key to wipe.
            partition_keys (Sequence[str]): Partition keys to wipe.
        """
        from dagster._core.events import AssetWipedData, DagsterEvent, DagsterEventType
        from dagster._core.instance.utils import RUNLESS_JOB_NAME, RUNLESS_RUN_ID

        self._instance._event_storage.wipe_asset_partitions(asset_key, partition_keys)  # noqa: SLF001
        self._instance.report_dagster_event(
            DagsterEvent(
                event_type_value=DagsterEventType.ASSET_WIPED.value,
                event_specific_data=AssetWipedData(
                    asset_key=asset_key, partition_keys=partition_keys
                ),
                job_name=RUNLESS_JOB_NAME,
            ),
            run_id=RUNLESS_RUN_ID,
        )

    def get_asset_records(
        self, asset_keys: Optional[Sequence["AssetKey"]] = None
    ) -> Sequence["AssetRecord"]:
        """Return an `AssetRecord` for each of the given asset keys.
        Moved from DagsterInstance.get_asset_records().

        Args:
            asset_keys (Optional[Iterable[AssetKey]]): List of asset keys to retrieve records for.

        Returns:
            Sequence[AssetRecord]: List of asset records.
        """
        return self._instance._event_storage.get_asset_records(asset_keys)  # noqa: SLF001

    def get_event_tags_for_asset(
        self,
        asset_key: "AssetKey",
        filter_tags: Optional[Mapping[str, str]] = None,
        filter_event_id: Optional[int] = None,
    ) -> Sequence[Mapping[str, str]]:
        """Fetches asset event tags for the given asset key.
        Moved from DagsterInstance.get_event_tags_for_asset().

        If filter_tags is provided, searches for events containing all of the filter tags. Then,
        returns all tags for those events. This enables searching for multipartitioned asset
        partition tags with a fixed dimension value, e.g. all of the tags for events where
        "country" == "US".

        If filter_event_id is provided, searches for the event with the provided event_id.

        Returns a list of dicts, where each dict is a mapping of tag key to tag value for a
        single event.
        """
        return self._instance._event_storage.get_event_tags_for_asset(  # noqa: SLF001
            asset_key, filter_tags, filter_event_id
        )

    def get_latest_planned_materialization_info(
        self,
        asset_key: "AssetKey",
        partition: Optional[str] = None,
    ) -> Optional["PlannedMaterializationInfo"]:
        """Get latest planned materialization info.
        Moved from DagsterInstance.get_latest_planned_materialization_info().
        """
        return self._instance._event_storage.get_latest_planned_materialization_info(  # noqa: SLF001
            asset_key, partition
        )

    def get_materialized_partitions(
        self,
        asset_key: "AssetKey",
        before_cursor: Optional[int] = None,
        after_cursor: Optional[int] = None,
    ) -> set[str]:
        """Get materialized partitions for an asset - moved from DagsterInstance.get_materialized_partitions()."""
        return self._instance._event_storage.get_materialized_partitions(  # noqa: SLF001
            asset_key, before_cursor=before_cursor, after_cursor=after_cursor
        )

    def get_latest_storage_id_by_partition(
        self,
        asset_key: "AssetKey",
        event_type: "DagsterEventType",
        partitions: Optional[set[str]] = None,
    ) -> Mapping[str, int]:
        """Fetch the latest materialization storage id for each partition for a given asset key.
        Moved from DagsterInstance.get_latest_storage_id_by_partition().

        Returns a mapping of partition to storage id.
        """
        return self._instance._event_storage.get_latest_storage_id_by_partition(  # noqa: SLF001
            asset_key, event_type, partitions
        )

    def fetch_planned_materializations(
        self,
        records_filter: Union["AssetKey", "AssetRecordsFilter"],
        limit: int,
        cursor: Optional[str] = None,
        ascending: bool = False,
    ) -> "EventRecordsResult":
        """Return a list of planned materialization records stored in the event log storage.
        Moved from DagsterInstance.fetch_planned_materializations().

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
        from dagster._core.event_api import EventLogCursor
        from dagster._core.events import DagsterEventType
        from dagster._core.storage.event_log.base import EventRecordsFilter, EventRecordsResult

        event_records_filter = (
            EventRecordsFilter(DagsterEventType.ASSET_MATERIALIZATION_PLANNED, records_filter)
            if isinstance(records_filter, AssetKey)
            else records_filter.to_event_records_filter(
                DagsterEventType.ASSET_MATERIALIZATION_PLANNED,
                cursor=cursor,
                ascending=ascending,
            )
        )
        records = self._instance._event_storage.get_event_records(  # noqa: SLF001
            event_records_filter, limit=limit, ascending=ascending
        )
        if records:
            new_cursor = EventLogCursor.from_storage_id(records[-1].storage_id).to_string()
        elif cursor:
            new_cursor = cursor
        else:
            new_cursor = EventLogCursor.from_storage_id(-1).to_string()
        has_more = len(records) == limit
        return EventRecordsResult(records, cursor=new_cursor, has_more=has_more)

    def get_latest_materialization_code_versions(
        self, asset_keys: Iterable["AssetKey"]
    ) -> Mapping["AssetKey", Optional[str]]:
        """Returns the code version used for the latest materialization of each of the provided
        assets. Moved from DagsterInstance.get_latest_materialization_code_versions().

        Args:
            asset_keys (Iterable[AssetKey]): The asset keys to find latest materialization code
                versions for.

        Returns:
            Mapping[AssetKey, Optional[str]]: A dictionary with a key for each of the provided asset
                keys. The values will be None if the asset has no materializations. If an asset does
                not have a code version explicitly assigned to its definitions, but was
                materialized, Dagster assigns the run ID as its code version.
        """
        from dagster._core.definitions.data_version import extract_data_provenance_from_entry

        result: dict[AssetKey, Optional[str]] = {}
        latest_materialization_events = self.get_latest_materialization_events(asset_keys)
        for asset_key in asset_keys:
            event_log_entry = latest_materialization_events.get(asset_key)
            if event_log_entry is None:
                result[asset_key] = None
            else:
                data_provenance = extract_data_provenance_from_entry(event_log_entry)
                result[asset_key] = data_provenance.code_version if data_provenance else None

        return result

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
        """Record an event log entry related to assets that does not belong to a Dagster run.
        Moved from DagsterInstance.report_runless_asset_event().
        """
        from dagster._core.events import AssetMaterialization

        if not isinstance(
            asset_event,
            (
                AssetMaterialization,
                AssetObservation,
                AssetCheckEvaluation,
                FreshnessStateEvaluation,
                FreshnessStateChange,
            ),
        ):
            from dagster._core.errors import DagsterInvariantViolationError

            raise DagsterInvariantViolationError(
                f"Received unexpected asset event type {asset_event}, expected"
                " AssetMaterialization, AssetObservation, AssetCheckEvaluation, FreshnessStateEvaluation or FreshnessStateChange"
            )

        return self._report_runless_asset_event(asset_event)

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
        """Use this directly over report_runless_asset_event to emit internal events.
        Moved from DagsterInstance._report_runless_asset_event().
        """
        from dagster._core.events import (
            AssetMaterialization,
            AssetObservationData,
            DagsterEvent,
            DagsterEventType,
            StepMaterializationData,
        )
        from dagster._core.instance.utils import RUNLESS_JOB_NAME, RUNLESS_RUN_ID

        if isinstance(asset_event, AssetMaterialization):
            event_type_value = DagsterEventType.ASSET_MATERIALIZATION.value
            data_payload = StepMaterializationData(asset_event)
        elif isinstance(asset_event, AssetCheckEvaluation):
            event_type_value = DagsterEventType.ASSET_CHECK_EVALUATION.value
            data_payload = asset_event
        elif isinstance(asset_event, AssetObservation):
            event_type_value = DagsterEventType.ASSET_OBSERVATION.value
            data_payload = AssetObservationData(asset_event)
        elif isinstance(asset_event, FreshnessStateEvaluation):
            event_type_value = DagsterEventType.FRESHNESS_STATE_EVALUATION.value
            data_payload = asset_event
        elif isinstance(asset_event, FreshnessStateChange):
            event_type_value = DagsterEventType.FRESHNESS_STATE_CHANGE.value
            data_payload = asset_event
        else:
            from dagster._core.errors import DagsterInvariantViolationError

            raise DagsterInvariantViolationError(
                f"Received unexpected asset event type {asset_event}, expected"
                " AssetMaterialization, AssetObservation, AssetCheckEvaluation, FreshnessStateEvaluation or FreshnessStateChange"
            )

        return self._instance.report_dagster_event(
            run_id=RUNLESS_RUN_ID,
            dagster_event=DagsterEvent(
                event_type_value=event_type_value,
                event_specific_data=data_payload,
                job_name=RUNLESS_JOB_NAME,
            ),
        )

    def get_asset_check_health_state_for_assets(
        self, asset_keys: Sequence["AssetKey"]
    ) -> Optional[Mapping["AssetKey", Optional["AssetCheckHealthState"]]]:
        """Get asset check health state for assets.
        Moved from DagsterInstance.get_asset_check_health_state_for_assets().
        """
        return None

    def get_asset_freshness_health_state_for_assets(
        self, asset_keys: Sequence["AssetKey"]
    ) -> Optional[Mapping["AssetKey", Optional["AssetFreshnessHealthState"]]]:
        """Get asset freshness health state for assets.
        Moved from DagsterInstance.get_asset_freshness_health_state_for_assets().
        """
        return None

    def get_asset_materialization_health_state_for_assets(
        self, asset_keys: Sequence["AssetKey"]
    ) -> Optional[Mapping["AssetKey", Optional["AssetMaterializationHealthState"]]]:
        """Get asset materialization health state for assets.
        Moved from DagsterInstance.get_asset_materialization_health_state_for_assets().
        """
        return None

    def get_minimal_asset_materialization_health_state_for_assets(
        self, asset_keys: Sequence["AssetKey"]
    ) -> Optional[Mapping["AssetKey", Optional["MinimalAssetMaterializationHealthState"]]]:
        """Get minimal asset materialization health state for assets.
        Moved from DagsterInstance.get_minimal_asset_materialization_health_state_for_assets().
        """
        return None
