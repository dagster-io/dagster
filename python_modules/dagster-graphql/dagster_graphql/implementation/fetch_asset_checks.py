from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Optional, Union, cast

from dagster import _check as check
from dagster._core.definitions.asset_checks.asset_check_spec import AssetCheckKey
from dagster._core.definitions.partitions.definition import (
    MultiPartitionsDefinition,
    PartitionsDefinition,
    TimeWindowPartitionsDefinition,
)
from dagster._core.definitions.partitions.subset import PartitionsSubset, TimeWindowPartitionsSubset
from dagster._core.event_api import PartitionKeyFilter
from dagster._core.events import ASSET_CHECK_EVENTS, DagsterEventType
from dagster._core.instance import DynamicPartitionsStore
from dagster._core.loader import LoadingContext
from dagster._core.remote_representation.handle import RepositoryHandle
from dagster._core.storage.asset_check_execution_record import (
    AssetCheckExecutionRecordStatus,
    AssetCheckExecutionResolvedStatus,
    AssetCheckInstanceSupport,
)
from dagster._core.storage.asset_check_state import AssetCheckState
from dagster._core.storage.dagster_run import RunRecord
from packaging import version

from dagster_graphql.implementation.partition_status_utils import (
    build_multi_partition_ranges_generic,
    build_time_partition_ranges_generic,
    extract_partition_keys_by_status,
)
from dagster_graphql.schema.asset_checks import (
    AssetCheckPartitionRangeStatus,
    GrapheneAssetCheckDefaultPartitionStatuses,
    GrapheneAssetCheckMultiPartitionRangeStatuses,
    GrapheneAssetCheckMultiPartitionStatuses,
    GrapheneAssetCheckNeedsAgentUpgradeError,
    GrapheneAssetCheckNeedsMigrationError,
    GrapheneAssetCheckNeedsUserCodeUpgrade,
    GrapheneAssetCheckTimePartitionRangeStatus,
    GrapheneAssetCheckTimePartitionStatuses,
)

if TYPE_CHECKING:
    from dagster_graphql.schema.asset_checks import GrapheneAssetCheckExecution
    from dagster_graphql.schema.entity_key import GrapheneAssetCheckHandle
    from dagster_graphql.schema.util import ResolveInfo


def check_asset_checks_support(
    graphene_info: "ResolveInfo", repository_handle: RepositoryHandle
) -> Union[
    GrapheneAssetCheckNeedsMigrationError,
    GrapheneAssetCheckNeedsUserCodeUpgrade,
    GrapheneAssetCheckNeedsAgentUpgradeError,
    None,
]:
    asset_check_support = graphene_info.context.instance.get_asset_check_support()
    if asset_check_support == AssetCheckInstanceSupport.NEEDS_MIGRATION:
        return GrapheneAssetCheckNeedsMigrationError(
            message="Asset checks require an instance migration. Run `dagster instance migrate`."
        )
    elif asset_check_support == AssetCheckInstanceSupport.NEEDS_AGENT_UPGRADE:
        return GrapheneAssetCheckNeedsAgentUpgradeError(
            "Asset checks require an agent upgrade to 1.5.0 or greater."
        )
    else:
        check.invariant(
            asset_check_support == AssetCheckInstanceSupport.SUPPORTED,
            f"Unexpected asset check support status {asset_check_support}",
        )

    library_versions = graphene_info.context.get_dagster_library_versions(
        repository_handle.location_name
    )
    code_location_version = (library_versions or {}).get("dagster")
    if code_location_version and version.parse(code_location_version) < version.parse("1.5"):
        return GrapheneAssetCheckNeedsUserCodeUpgrade(
            message=(
                "Asset checks require dagster>=1.5. Upgrade your dagster"
                " version for this code location."
            )
        )


def fetch_asset_check_executions(
    loading_context: LoadingContext,
    asset_check_key: AssetCheckKey,
    limit: int,
    cursor: Optional[str],
    partition_filter: Optional[PartitionKeyFilter],
) -> list["GrapheneAssetCheckExecution"]:
    from dagster_graphql.schema.asset_checks import GrapheneAssetCheckExecution

    check_records = loading_context.instance.event_log_storage.get_asset_check_execution_history(
        check_key=asset_check_key,
        limit=limit,
        cursor=int(cursor) if cursor else None,
        partition_filter=partition_filter,
    )

    RunRecord.prepare(
        loading_context,
        [r.run_id for r in check_records if r.status == AssetCheckExecutionRecordStatus.PLANNED],
    )

    return [GrapheneAssetCheckExecution(check_record) for check_record in check_records]


def get_asset_checks_for_run_id(
    graphene_info: "ResolveInfo", run_id: str
) -> Sequence["GrapheneAssetCheckHandle"]:
    from dagster_graphql.schema.entity_key import GrapheneAssetCheckHandle

    check.str_param(run_id, "run_id")

    records = graphene_info.context.instance.all_logs(run_id, of_type=ASSET_CHECK_EVENTS)

    asset_check_keys = set(
        [
            record.get_dagster_event().asset_check_evaluation_data.asset_check_key
            for record in records
            if record.is_dagster_event
            and record.get_dagster_event().event_type == DagsterEventType.ASSET_CHECK_EVALUATION
        ]
        + [
            record.get_dagster_event().asset_check_planned_data.asset_check_key
            for record in records
            if record.is_dagster_event
            and record.get_dagster_event().event_type
            == DagsterEventType.ASSET_CHECK_EVALUATION_PLANNED
        ]
    )
    return [
        GrapheneAssetCheckHandle(handle=asset_check_key)
        for asset_check_key in sorted(
            asset_check_keys, key=lambda key: key.name + "".join(key.asset_key.path)
        )
    ]


# Partition status builder functions


def build_asset_check_partition_statuses(
    key: AssetCheckKey,
    asset_check_state: AssetCheckState,
    partitions_def: PartitionsDefinition,
    dynamic_partitions_store: DynamicPartitionsStore,
) -> Union[
    GrapheneAssetCheckTimePartitionStatuses,
    GrapheneAssetCheckDefaultPartitionStatuses,
    GrapheneAssetCheckMultiPartitionStatuses,
]:
    """Build appropriate partition status type based on partitions definition.

    Decision tree:
    1. Extract subsets from partition_status.subsets for all 5 statuses
    2. Check first subset type:
       - TimeWindowPartitionsSubset → build_time_partition_statuses_for_checks()
       - MultiPartitionsDefinition in partitions_def → build_multi_partition_statuses_for_checks()
       - Otherwise → build_default_partition_statuses_for_checks()

    Note: Missing status is calculated on the frontend as the complement of all known statuses.
    """
    # Extract subsets for each status
    subsets = asset_check_state.subsets

    # Check if we have any subsets to determine the type
    first_subset = next((s.subset_value for s in subsets.values() if s is not None), None)

    # Decision based on subset type and partitions definition
    if first_subset is not None and isinstance(first_subset, TimeWindowPartitionsSubset):
        # Time partitions - use range compression
        return build_time_partition_statuses_for_checks(
            subsets={
                status: cast("TimeWindowPartitionsSubset", s.subset_value)
                for status, s in subsets.items()
                if s is not None
            },
            partitions_def=cast("TimeWindowPartitionsDefinition", partitions_def),
        )
    elif isinstance(partitions_def, MultiPartitionsDefinition):
        # Multi-partitions - use 2D run-length encoding
        return build_multi_partition_statuses_for_checks(
            key=key,
            subsets={status: s.subset_value for status, s in subsets.items() if s is not None},
            partitions_def=partitions_def,
            dynamic_partitions_store=dynamic_partitions_store,
        )
    else:
        # Default partitions - simple partition key lists
        return build_default_partition_statuses_for_checks(
            subsets={status: s.subset_value for status, s in subsets.items() if s is not None},
            partitions_def=partitions_def,
            dynamic_partitions_store=dynamic_partitions_store,
        )


def build_time_partition_statuses_for_checks(
    subsets: Mapping[AssetCheckExecutionResolvedStatus, TimeWindowPartitionsSubset],
    partitions_def: TimeWindowPartitionsDefinition,
) -> GrapheneAssetCheckTimePartitionStatuses:
    """Build time-based ranges for all 5 statuses.

    Uses shared utility to convert time window subsets to generic ranges,
    then converts to GraphQL-specific types.

    Note: Missing status is calculated on the frontend as the complement of all known statuses.
    """
    # Use shared utility to build generic ranges
    generic_ranges = build_time_partition_ranges_generic(subsets)

    # Convert generic ranges to GraphQL types
    graphene_ranges = [
        GrapheneAssetCheckTimePartitionRangeStatus(
            startTime=r.start_time,
            endTime=r.end_time,
            startKey=r.start_key,
            endKey=r.end_key,
            status=map_check_status_to_range_status(r.status),
        )
        for r in generic_ranges
    ]

    return GrapheneAssetCheckTimePartitionStatuses(ranges=graphene_ranges)


def build_default_partition_statuses_for_checks(
    subsets: Mapping[AssetCheckExecutionResolvedStatus, PartitionsSubset],
    partitions_def: PartitionsDefinition,
    dynamic_partitions_store: DynamicPartitionsStore,
) -> GrapheneAssetCheckDefaultPartitionStatuses:
    """Extract partition keys for each status.

    Uses shared utility to extract partition keys by status,
    then maps to GraphQL field names.

    Note: Missing status is calculated on the frontend as the complement of all known statuses.
    """
    # Use shared utility to extract partition keys
    keys_by_status = extract_partition_keys_by_status(
        subsets, partitions_def, dynamic_partitions_store
    )

    return GrapheneAssetCheckDefaultPartitionStatuses(
        succeededPartitions=keys_by_status.get(AssetCheckExecutionResolvedStatus.SUCCEEDED, []),
        failedPartitions=keys_by_status.get(AssetCheckExecutionResolvedStatus.FAILED, []),
        inProgressPartitions=keys_by_status.get(AssetCheckExecutionResolvedStatus.IN_PROGRESS, []),
        skippedPartitions=keys_by_status.get(AssetCheckExecutionResolvedStatus.SKIPPED, []),
        executionFailedPartitions=keys_by_status.get(
            AssetCheckExecutionResolvedStatus.EXECUTION_FAILED, []
        ),
    )


def build_multi_partition_statuses_for_checks(
    key: AssetCheckKey,
    subsets: Mapping[AssetCheckExecutionResolvedStatus, PartitionsSubset],
    partitions_def: MultiPartitionsDefinition,
    dynamic_partitions_store: DynamicPartitionsStore,
) -> GrapheneAssetCheckMultiPartitionStatuses:
    """Build 2D run-length encoded statuses.

    Uses shared utility for 2D run-length encoding algorithm,
    then converts to GraphQL-specific types.

    Note: Missing status is calculated on the frontend as the complement of all known statuses.
    """
    from dagster._core.asset_graph_view.serializable_entity_subset import SerializableEntitySubset

    # Define recursive builder for secondary dimension
    def build_secondary_dim(
        secondary_subsets: Mapping[AssetCheckExecutionResolvedStatus, PartitionsSubset],
    ):
        # Convert to SerializableEntitySubset for recursive call
        secondary_serializable_subsets = {}
        for status, secondary_subset in secondary_subsets.items():
            secondary_serializable_subsets[status] = SerializableEntitySubset.from_coercible_value(
                key,
                list(secondary_subset.get_partition_keys()),
                partitions_def.secondary_dimension.partitions_def,
            )

        # Build temporary cache value for secondary dimension
        temp_cache_value = AssetCheckState(
            latest_storage_id=0,
            subsets=secondary_serializable_subsets,
            in_progress_runs={},
        )

        # Recursively build secondary dimension statuses
        return build_asset_check_partition_statuses(
            key=key,
            asset_check_state=temp_cache_value,
            partitions_def=partitions_def.secondary_dimension.partitions_def,
            dynamic_partitions_store=dynamic_partitions_store,
        )

    # Use shared utility to build generic multi-partition ranges
    generic_ranges = build_multi_partition_ranges_generic(
        subsets,
        partitions_def,
        dynamic_partitions_store,
        build_secondary_dim,
    )

    # Convert generic ranges to GraphQL types
    graphene_ranges = [
        GrapheneAssetCheckMultiPartitionRangeStatuses(
            primaryDimStartKey=r.primary_dim_start_key,
            primaryDimEndKey=r.primary_dim_end_key,
            primaryDimStartTime=r.primary_dim_start_time,
            primaryDimEndTime=r.primary_dim_end_time,
            secondaryDim=r.secondary_dim,
        )
        for r in generic_ranges
    ]

    return GrapheneAssetCheckMultiPartitionStatuses(
        ranges=graphene_ranges,
        primaryDimensionName=partitions_def.primary_dimension.name,
    )


# Helper functions


def map_check_status_to_range_status(
    status: AssetCheckExecutionResolvedStatus,
) -> AssetCheckPartitionRangeStatus:
    """Map internal status enum to GraphQL range status enum."""
    mapping = {
        AssetCheckExecutionResolvedStatus.SUCCEEDED: AssetCheckPartitionRangeStatus.SUCCEEDED,
        AssetCheckExecutionResolvedStatus.FAILED: AssetCheckPartitionRangeStatus.FAILED,
        AssetCheckExecutionResolvedStatus.IN_PROGRESS: AssetCheckPartitionRangeStatus.IN_PROGRESS,
        AssetCheckExecutionResolvedStatus.SKIPPED: AssetCheckPartitionRangeStatus.SKIPPED,
        AssetCheckExecutionResolvedStatus.EXECUTION_FAILED: AssetCheckPartitionRangeStatus.EXECUTION_FAILED,
    }
    return mapping[status]
