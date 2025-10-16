"""Asset methods implementation - consolidated from AssetDomain and AssetMixin."""

import os
from collections.abc import Iterable, Mapping, Sequence
from typing import TYPE_CHECKING, Literal, Optional, Union

import dagster._check as check
from dagster._annotations import deprecated
from dagster._core.definitions.asset_checks.asset_check_evaluation import AssetCheckEvaluation
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.events import AssetObservation
from dagster._core.definitions.freshness import FreshnessStateChange, FreshnessStateEvaluation
from dagster._utils import traced

if TYPE_CHECKING:
    from dagster._core.definitions.asset_checks.asset_check_spec import AssetCheckKey
    from dagster._core.definitions.asset_health.asset_check_health import AssetCheckHealthState
    from dagster._core.definitions.asset_health.asset_freshness_health import (
        AssetFreshnessHealthState,
    )
    from dagster._core.definitions.asset_health.asset_materialization_health import (
        AssetMaterializationHealthState,
        MinimalAssetMaterializationHealthState,
    )
    from dagster._core.definitions.freshness import FreshnessStateRecord
    from dagster._core.definitions.partitions.definition.partitions_definition import (
        PartitionsDefinition,
    )
    from dagster._core.event_api import EventLogRecord, EventRecordsResult
    from dagster._core.events import AssetMaterialization, DagsterEventType
    from dagster._core.events.log import EventLogEntry
    from dagster._core.instance.instance import DagsterInstance
    from dagster._core.storage.asset_check_execution_record import (
        AssetCheckExecutionRecord,
        AssetCheckInstanceSupport,
    )
    from dagster._core.storage.event_log.base import (
        AssetRecord,
        AssetRecordsFilter,
        PlannedMaterializationInfo,
    )
    from dagster._core.storage.partition_status_cache import (
        AssetPartitionStatus,
        AssetStatusCacheValue,
    )

StreamlineName = Literal[
    "asset-materialization-health", "asset-check-health", "asset-freshness-health"
]


class AssetMethods:
    """Mixin class containing asset-related functionality for DagsterInstance.

    This class consolidates asset operations from both AssetDomain and AssetMixin,
    providing methods for asset management, materialization tracking, and health monitoring.
    All methods are implemented as instance methods that DagsterInstance inherits.
    """

    # These methods/properties are provided by DagsterInstance
    # (no abstract declarations needed since DagsterInstance already implements them)

    @property
    def _instance(self) -> "DagsterInstance":
        """Cast self to DagsterInstance for type-safe access to instance methods and properties."""
        from dagster._core.instance.instance import DagsterInstance

        return check.inst(self, DagsterInstance)

    # Private member access wrapper with consolidated type: ignore
    @property
    def _event_storage_impl(self):
        """Access to event storage."""
        return self._instance._event_storage  # noqa: SLF001

    def can_read_asset_status_cache(self) -> bool:
        """Check if asset status cache can be read - moved from AssetDomain.can_read_asset_status_cache()."""
        return self._event_storage_impl.can_read_asset_status_cache()

    def update_asset_cached_status_data(
        self, asset_key: "AssetKey", cache_values: "AssetStatusCacheValue"
    ) -> None:
        """Update asset cached status data - moved from AssetDomain.update_asset_cached_status_data()."""
        self._event_storage_impl.update_asset_cached_status_data(asset_key, cache_values)

    def wipe_asset_cached_status(self, asset_keys: Sequence["AssetKey"]) -> None:
        """Wipe asset cached status - moved from AssetDomain.wipe_asset_cached_status()."""
        check.list_param(asset_keys, "asset_keys", of_type=AssetKey)
        for asset_key in asset_keys:
            self._event_storage_impl.wipe_asset_cached_status(asset_key)

    def all_asset_keys(self) -> Sequence["AssetKey"]:
        """Get all asset keys - moved from AssetDomain.all_asset_keys()."""
        return self._event_storage_impl.all_asset_keys()

    @traced
    def get_latest_materialization_events(
        self, asset_keys: Iterable["AssetKey"]
    ) -> Mapping["AssetKey", Optional["EventLogEntry"]]:
        """Get latest materialization events - moved from AssetDomain.get_latest_materialization_events()."""
        return self._event_storage_impl.get_latest_materialization_events(asset_keys)

    @traced
    def get_latest_asset_check_evaluation_record(
        self, asset_check_key: "AssetCheckKey"
    ) -> Optional["AssetCheckExecutionRecord"]:
        """Get latest asset check evaluation record - moved from AssetDomain.get_latest_asset_check_evaluation_record()."""
        return self._event_storage_impl.get_latest_asset_check_execution_by_key(
            [asset_check_key]
        ).get(asset_check_key)

    def fetch_failed_materializations(
        self,
        records_filter: Union["AssetKey", "AssetRecordsFilter"],
        limit: int,
        cursor: Optional[str] = None,
        ascending: bool = False,
    ) -> "EventRecordsResult":
        """Return a list of AssetFailedToMaterialization records stored in the event log storage.
        Moved from AssetDomain.fetch_failed_materializations().

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
        return self._event_storage_impl.fetch_failed_materializations(
            records_filter, limit, cursor, ascending
        )

    def wipe_asset_partitions(
        self,
        asset_key: "AssetKey",
        partition_keys: Sequence[str],
    ) -> None:
        """Wipes asset event history from the event log for the given asset key and partition keys.
        Moved from AssetDomain.wipe_asset_partitions().

        Args:
            asset_key (AssetKey): Asset key to wipe.
            partition_keys (Sequence[str]): Partition keys to wipe.
        """
        from dagster._core.events import AssetWipedData, DagsterEvent, DagsterEventType
        from dagster._core.instance.utils import RUNLESS_JOB_NAME, RUNLESS_RUN_ID

        self._event_storage_impl.wipe_asset_partitions(asset_key, partition_keys)
        self.report_dagster_event(  # type: ignore[attr-defined]
            DagsterEvent(
                event_type_value=DagsterEventType.ASSET_WIPED.value,
                event_specific_data=AssetWipedData(
                    asset_key=asset_key, partition_keys=partition_keys
                ),
                job_name=RUNLESS_JOB_NAME,
            ),
            run_id=RUNLESS_RUN_ID,
        )

    def get_event_tags_for_asset(
        self,
        asset_key: "AssetKey",
        filter_tags: Optional[Mapping[str, str]] = None,
        filter_event_id: Optional[int] = None,
    ) -> Sequence[Mapping[str, str]]:
        """Fetches asset event tags for the given asset key.
        Moved from AssetDomain.get_event_tags_for_asset().

        If filter_tags is provided, searches for events containing all of the filter tags. Then,
        returns all tags for those events. This enables searching for multipartitioned asset
        partition tags with a fixed dimension value, e.g. all of the tags for events where
        "country" == "US".

        If filter_event_id is provided, searches for the event with the provided event_id.

        Returns a list of dicts, where each dict is a mapping of tag key to tag value for a
        single event.
        """
        return self._event_storage_impl.get_event_tags_for_asset(
            asset_key, filter_tags, filter_event_id
        )

    @traced
    def get_latest_planned_materialization_info(
        self,
        asset_key: "AssetKey",
        partition: Optional[str] = None,
    ) -> Optional["PlannedMaterializationInfo"]:
        """Get latest planned materialization info.
        Moved from AssetDomain.get_latest_planned_materialization_info().
        """
        return self._event_storage_impl.get_latest_planned_materialization_info(
            asset_key, partition
        )

    @traced
    def get_materialized_partitions(
        self,
        asset_key: "AssetKey",
        before_cursor: Optional[int] = None,
        after_cursor: Optional[int] = None,
    ) -> set[str]:
        """Get materialized partitions for an asset - moved from AssetDomain.get_materialized_partitions()."""
        return self._event_storage_impl.get_materialized_partitions(
            asset_key, before_cursor=before_cursor, after_cursor=after_cursor
        )

    @traced
    def get_latest_storage_id_by_partition(
        self,
        asset_key: "AssetKey",
        event_type: "DagsterEventType",
        partitions: Optional[set[str]] = None,
    ) -> Mapping[str, int]:
        """Fetch the latest materialization storage id for each partition for a given asset key.
        Moved from AssetDomain.get_latest_storage_id_by_partition().

        Returns a mapping of partition to storage id.
        """
        return self._event_storage_impl.get_latest_storage_id_by_partition(
            asset_key, event_type, partitions
        )

    @deprecated(breaking_version="2.0")
    def fetch_planned_materializations(
        self,
        records_filter: Union["AssetKey", "AssetRecordsFilter"],
        limit: int,
        cursor: Optional[str] = None,
        ascending: bool = False,
    ) -> "EventRecordsResult":
        """Return a list of planned materialization records stored in the event log storage.
        Moved from AssetDomain.fetch_planned_materializations().

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
        records = self._event_storage_impl.get_event_records(
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
        Moved from AssetDomain._report_runless_asset_event().
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

        return self.report_dagster_event(  # type: ignore[attr-defined]
            run_id=RUNLESS_RUN_ID,
            dagster_event=DagsterEvent(
                event_type_value=event_type_value,
                event_specific_data=data_payload,
                job_name=RUNLESS_JOB_NAME,
            ),
        )

    def get_asset_check_health_state_for_assets(
        self, asset_keys: Sequence["AssetKey"]
    ) -> Mapping["AssetKey", Optional["AssetCheckHealthState"]]:
        """Get asset check health state for assets.
        Moved from AssetDomain.get_asset_check_health_state_for_assets().
        """
        return {asset_key: None for asset_key in asset_keys}

    def get_asset_freshness_health_state_for_assets(
        self, asset_keys: Sequence["AssetKey"]
    ) -> Mapping["AssetKey", Optional["AssetFreshnessHealthState"]]:
        """Get asset freshness health state for assets.
        Moved from AssetDomain.get_asset_freshness_health_state_for_assets().
        """
        return {asset_key: None for asset_key in asset_keys}

    def get_asset_materialization_health_state_for_assets(
        self, asset_keys: Sequence["AssetKey"]
    ) -> Mapping["AssetKey", Optional["AssetMaterializationHealthState"]]:
        """Get asset materialization health state for assets.
        Moved from AssetDomain.get_asset_materialization_health_state_for_assets().
        """
        return {asset_key: None for asset_key in asset_keys}

    def get_minimal_asset_materialization_health_state_for_assets(
        self, asset_keys: Sequence["AssetKey"]
    ) -> Mapping["AssetKey", Optional["MinimalAssetMaterializationHealthState"]]:
        """Get minimal asset materialization health state for assets.
        Moved from AssetDomain.get_minimal_asset_materialization_health_state_for_assets().
        """
        return {asset_key: None for asset_key in asset_keys}

    def get_latest_data_version_record(
        self,
        key: AssetKey,
        is_source: Optional[bool] = None,
        partition_key: Optional[str] = None,
        before_cursor: Optional[int] = None,
        after_cursor: Optional[int] = None,
    ) -> Optional["EventLogRecord"]:
        """Get the latest data version record for an asset.
        Moved from AssetDomain.get_latest_data_version_record().

        Args:
            key (AssetKey): The asset key to get the latest data version record for.
            is_source (Optional[bool]): Whether the asset is a source asset. If True, fetches
                observations. If False, fetches materializations. If None, fetches materializations
                first, then observations if no materialization found.
            partition_key (Optional[str]): The partition key to filter by.
            before_cursor (Optional[int]): Only return records with storage ID less than this.
            after_cursor (Optional[int]): Only return records with storage ID greater than this.

        Returns:
            Optional[EventLogRecord]: The latest data version record, or None if not found.
        """
        from dagster._core.storage.event_log.base import AssetRecordsFilter

        records_filter = AssetRecordsFilter(
            asset_key=key,
            asset_partitions=[partition_key] if partition_key else None,
            before_storage_id=before_cursor,
            after_storage_id=after_cursor,
        )

        if is_source is True:
            # this is a source asset, fetch latest observation record
            return next(
                iter(self.fetch_observations(records_filter, limit=1).records),  # type: ignore[attr-defined]
                None,
            )

        elif is_source is False:
            # this is not a source asset, fetch latest materialization record
            return next(
                iter(self.fetch_materializations(records_filter, limit=1).records),
                None,
            )

        else:
            assert is_source is None
            # if is_source is None, the requested key could correspond to either a source asset or
            # materializable asset. If there is a non-null materialization, we are dealing with a
            # materializable asset and should just return that.  If not, we should check for any
            # observation records that may match.

            materialization = next(
                iter(self.fetch_materializations(records_filter, limit=1).records),
                None,
            )
            if materialization:
                return materialization
            return next(
                iter(self.fetch_observations(records_filter, limit=1).records),  # type: ignore[attr-defined]
                None,
            )

    # Additional methods from AssetMixin that don't duplicate AssetDomain methods

    def get_freshness_state_records(
        self, keys: Sequence["AssetKey"]
    ) -> Mapping["AssetKey", "FreshnessStateRecord"]:
        """Get freshness state records - moved from AssetMixin.get_freshness_state_records()."""
        return self._event_storage_impl.get_freshness_state_records(keys)

    def get_asset_check_support(self) -> "AssetCheckInstanceSupport":
        """Get asset check support - moved from AssetMixin.get_asset_check_support()."""
        from dagster._core.storage.asset_check_execution_record import AssetCheckInstanceSupport

        return (
            AssetCheckInstanceSupport.SUPPORTED
            if self._event_storage_impl.supports_asset_checks
            else AssetCheckInstanceSupport.NEEDS_MIGRATION
        )

    def dagster_asset_health_queries_supported(self) -> bool:
        """Check if asset health queries are supported - moved from AssetMixin.dagster_asset_health_queries_supported()."""
        return False

    def can_read_failure_events_for_asset(self, _asset_record: "AssetRecord") -> bool:
        """Check if failure events can be read for asset - moved from AssetMixin.can_read_failure_events_for_asset()."""
        return False

    def can_read_asset_failure_events(self) -> bool:
        """Check if asset failure events can be read - moved from AssetMixin.can_read_asset_failure_events()."""
        return False

    def internal_asset_freshness_enabled(self) -> bool:
        """Check if internal asset freshness is enabled - moved from AssetMixin.internal_asset_freshness_enabled()."""
        return os.getenv("DAGSTER_ASSET_FRESHNESS_ENABLED", "").lower() == "true"

    def streamline_read_asset_health_supported(self, streamline_name: StreamlineName) -> bool:
        """Check if streamline read asset health is supported - moved from AssetMixin.streamline_read_asset_health_supported()."""
        return False

    def streamline_read_asset_health_required(self, streamline_name: StreamlineName) -> bool:
        """Check if streamline read asset health is required - moved from AssetMixin.streamline_read_asset_health_required()."""
        return False

    # Implementation methods for public API methods (called from DagsterInstance public methods)

    def fetch_materializations(
        self,
        records_filter: Union["AssetKey", "AssetRecordsFilter"],
        limit: int,
        cursor: Optional[str] = None,
        ascending: bool = False,
    ) -> "EventRecordsResult":
        """Return a list of materialization records stored in the event log storage.
        Moved from AssetDomain.fetch_materializations().

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
        return self._event_storage_impl.fetch_materializations(
            records_filter, limit, cursor, ascending
        )

    def get_asset_keys(
        self,
        prefix: Optional[Sequence[str]] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> Sequence["AssetKey"]:
        """Return a filtered subset of asset keys managed by this instance.
        Moved from AssetDomain.get_asset_keys().

        Args:
            prefix (Optional[Sequence[str]]): Return only assets having this key prefix.
            limit (Optional[int]): Maximum number of keys to return.
            cursor (Optional[str]): Cursor to use for pagination.

        Returns:
            Sequence[AssetKey]: List of asset keys.
        """
        return self._event_storage_impl.get_asset_keys(prefix=prefix, limit=limit, cursor=cursor)

    def get_asset_records(
        self, asset_keys: Optional[Sequence["AssetKey"]] = None
    ) -> Sequence["AssetRecord"]:
        """Return an `AssetRecord` for each of the given asset keys.
        Moved from AssetDomain.get_asset_records().

        Args:
            asset_keys (Optional[Sequence[AssetKey]]): List of asset keys to retrieve records for.

        Returns:
            Sequence[AssetRecord]: List of asset records.
        """
        return self._event_storage_impl.get_asset_records(asset_keys)

    def get_latest_materialization_code_versions(
        self, asset_keys: Iterable["AssetKey"]
    ) -> Mapping["AssetKey", Optional[str]]:
        """Returns the code version used for the latest materialization of each of the provided
        assets. Moved from AssetDomain.get_latest_materialization_code_versions().

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

    def get_latest_materialization_event(self, asset_key: "AssetKey") -> Optional["EventLogEntry"]:
        """Fetch the latest materialization event for the given asset key.
        Moved from AssetDomain.get_latest_materialization_event().

        Args:
            asset_key (AssetKey): Asset key to return materialization for.

        Returns:
            Optional[EventLogEntry]: The latest materialization event for the given asset
                key, or `None` if the asset has not been materialized.
        """
        return self._event_storage_impl.get_latest_materialization_events([asset_key]).get(
            asset_key
        )

    def get_status_by_partition(
        self,
        asset_key: AssetKey,
        partition_keys: Sequence[str],
        partitions_def: "PartitionsDefinition",
    ) -> Optional[Mapping[str, "AssetPartitionStatus"]]:
        """Get the current status of provided partition_keys for the provided asset.
        Moved from AssetDomain.get_status_by_partition().

        Args:
            asset_key (AssetKey): The asset to get per-partition status for.
            partition_keys (Sequence[str]): The partitions to get status for.
            partitions_def (PartitionsDefinition): The PartitionsDefinition of the asset to get
                per-partition status for.

        Returns:
            Optional[Mapping[str, AssetPartitionStatus]]: status for each partition key

        """
        from typing import cast

        from dagster._core.storage.partition_status_cache import (
            AssetPartitionStatus,
            AssetStatusCacheValue,
            get_and_update_asset_status_cache_value,
        )

        # Cast is safe since this mixin is only used by DagsterInstance
        cached_value = get_and_update_asset_status_cache_value(
            cast("DagsterInstance", self), asset_key, partitions_def
        )

        if isinstance(cached_value, AssetStatusCacheValue):
            materialized_partitions = cached_value.deserialize_materialized_partition_subsets(
                partitions_def
            )
            failed_partitions = cached_value.deserialize_failed_partition_subsets(partitions_def)
            in_progress_partitions = cached_value.deserialize_in_progress_partition_subsets(
                partitions_def
            )

            status_by_partition = {}

            for partition_key in partition_keys:
                if partition_key in in_progress_partitions:
                    status_by_partition[partition_key] = AssetPartitionStatus.IN_PROGRESS
                elif partition_key in failed_partitions:
                    status_by_partition[partition_key] = AssetPartitionStatus.FAILED
                elif partition_key in materialized_partitions:
                    status_by_partition[partition_key] = AssetPartitionStatus.MATERIALIZED
                else:
                    status_by_partition[partition_key] = None

            return status_by_partition

    def has_asset_key(self, asset_key: "AssetKey") -> bool:
        """Return true if this instance manages the given asset key.
        Moved from AssetDomain.has_asset_key().

        Args:
            asset_key (AssetKey): Asset key to check.
        """
        return self._event_storage_impl.has_asset_key(asset_key)

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
        Moved from AssetDomain.report_runless_asset_event().
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

    def wipe_assets(self, asset_keys: Sequence["AssetKey"]) -> None:
        """Wipes asset event history from the event log for the given asset keys.
        Moved from AssetDomain.wipe_assets().

        Args:
            asset_keys (Sequence[AssetKey]): Asset keys to wipe.
        """
        from dagster._core.events import AssetWipedData, DagsterEvent, DagsterEventType
        from dagster._core.instance.utils import RUNLESS_JOB_NAME, RUNLESS_RUN_ID

        check.list_param(asset_keys, "asset_keys", of_type=AssetKey)
        for asset_key in asset_keys:
            self._event_storage_impl.wipe_asset(asset_key)
            self.report_dagster_event(  # type: ignore[attr-defined]
                DagsterEvent(
                    event_type_value=DagsterEventType.ASSET_WIPED.value,
                    event_specific_data=AssetWipedData(asset_key=asset_key, partition_keys=None),
                    job_name=RUNLESS_JOB_NAME,
                ),
                run_id=RUNLESS_RUN_ID,
            )
