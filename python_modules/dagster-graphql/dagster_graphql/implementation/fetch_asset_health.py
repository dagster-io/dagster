from typing import TYPE_CHECKING, Optional

import dagster._check as check
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.freshness import FreshnessState
from dagster._core.storage.event_log.base import AssetRecord
from dagster._streamline.asset_check_health import AssetCheckHealthState
from dagster._streamline.asset_freshness_health import AssetFreshnessHealthState
from dagster._streamline.asset_health import AssetHealthStatus
from dagster._streamline.asset_materialization_health import AssetMaterializationHealthState

if TYPE_CHECKING:
    from dagster_graphql.schema.asset_health import (
        GrapheneAssetHealthCheckMeta,
        GrapheneAssetHealthFreshnessMeta,
        GrapheneAssetHealthMaterializationMeta,
    )
    from dagster_graphql.schema.util import ResolveInfo


async def get_asset_check_status_and_metadata(
    graphene_info: "ResolveInfo",
    asset_key: AssetKey,
) -> tuple[str, Optional["GrapheneAssetHealthCheckMeta"]]:
    """Converts an AssetCheckHealthState object to a GrapheneAssetHealthStatus and the metadata
    needed to power the UIs.
    """
    from dagster_graphql.schema.asset_health import (
        GrapheneAssetHealthCheckDegradedMeta,
        GrapheneAssetHealthCheckUnknownMeta,
        GrapheneAssetHealthCheckWarningMeta,
        GrapheneAssetHealthStatus,
    )

    if graphene_info.context.instance.streamline_read_asset_health_supported():
        asset_check_health_state = (
            graphene_info.context.instance.get_asset_check_health_state_for_asset(asset_key)
        )
        if asset_check_health_state is None:
            # asset_check_health_state_for is only None if no are defined on the asset
            return GrapheneAssetHealthStatus.NOT_APPLICABLE, None
    else:
        remote_check_nodes = graphene_info.context.asset_graph.get_checks_for_asset(asset_key)
        asset_check_health_state = await AssetCheckHealthState.compute_for_asset_checks(
            {remote_check_node.asset_check.key for remote_check_node in remote_check_nodes},
            graphene_info.context,
        )

    if asset_check_health_state.health_status == AssetHealthStatus.HEALTHY:
        return GrapheneAssetHealthStatus.HEALTHY, None
    if asset_check_health_state.health_status == AssetHealthStatus.WARNING:
        return (
            GrapheneAssetHealthStatus.WARNING,
            GrapheneAssetHealthCheckWarningMeta(
                numWarningChecks=len(asset_check_health_state.warning_checks),
                totalNumChecks=len(asset_check_health_state.all_checks),
            ),
        )
    if asset_check_health_state.health_status == AssetHealthStatus.DEGRADED:
        return (
            GrapheneAssetHealthStatus.DEGRADED,
            GrapheneAssetHealthCheckDegradedMeta(
                numFailedChecks=len(asset_check_health_state.failing_checks),
                numWarningChecks=len(asset_check_health_state.warning_checks),
                totalNumChecks=len(asset_check_health_state.all_checks),
            ),
        )
    if asset_check_health_state.health_status == AssetHealthStatus.UNKNOWN:
        return (
            GrapheneAssetHealthStatus.UNKNOWN,
            GrapheneAssetHealthCheckUnknownMeta(
                numNotExecutedChecks=len(asset_check_health_state.all_checks)
                - len(asset_check_health_state.passing_checks)
                - len(asset_check_health_state.failing_checks)
                - len(asset_check_health_state.warning_checks),
                totalNumChecks=len(asset_check_health_state.all_checks),
            ),
        )
    elif asset_check_health_state.health_status == AssetHealthStatus.NOT_APPLICABLE:
        return GrapheneAssetHealthStatus.NOT_APPLICABLE, None
    else:
        check.failed(
            f"Unexpected asset check health status: {asset_check_health_state.health_status}"
        )


async def get_freshness_status_and_metadata(
    graphene_info: "ResolveInfo", asset_key: AssetKey
) -> tuple[str, Optional["GrapheneAssetHealthFreshnessMeta"]]:
    """Gets an AssetFreshnessHealthState object for an asset, either via streamline or by computing
    it based on the state of the DB. Then converts it to a GrapheneAssetHealthStatus and the metadata
    needed to power the UIs. Metadata is fetched from the AssetLatestMaterializationState object, again
    either via streamline or by computing it based on the state of the DB.
    """
    from dagster_graphql.schema.asset_health import (
        GrapheneAssetHealthFreshnessMeta,
        GrapheneAssetHealthStatus,
    )

    if graphene_info.context.instance.streamline_read_asset_health_supported():
        asset_freshness_health_state = (
            graphene_info.context.instance.get_asset_freshness_health_state_for_asset(asset_key)
        )
        if asset_freshness_health_state is None:
            # if the freshness state is None, it means that the asset hasn't been processed by streamline
            # yet. Return UNKNOWN and rely on the freshness daemon to update the state on the next iteration.
            return GrapheneAssetHealthStatus.UNKNOWN, None
    else:
        if graphene_info.context.asset_graph.get(asset_key).internal_freshness_policy is None:
            return GrapheneAssetHealthStatus.NOT_APPLICABLE, None
        asset_freshness_health_state = AssetFreshnessHealthState.compute_for_asset(
            asset_key,
            graphene_info.context,
        )

    asset_record = await AssetRecord.gen(graphene_info.context, asset_key)
    materialization_timestamp = (
        asset_record.asset_entry.last_materialization.timestamp
        if asset_record
        and asset_record.asset_entry
        and asset_record.asset_entry.last_materialization
        else None
    )

    if asset_freshness_health_state.freshness_state == FreshnessState.PASS:
        return GrapheneAssetHealthStatus.HEALTHY, GrapheneAssetHealthFreshnessMeta(
            lastMaterializedTimestamp=materialization_timestamp,
        )
    if asset_freshness_health_state.freshness_state == FreshnessState.WARN:
        return GrapheneAssetHealthStatus.WARNING, GrapheneAssetHealthFreshnessMeta(
            lastMaterializedTimestamp=materialization_timestamp,
        )
    if asset_freshness_health_state.freshness_state == FreshnessState.FAIL:
        return GrapheneAssetHealthStatus.DEGRADED, GrapheneAssetHealthFreshnessMeta(
            lastMaterializedTimestamp=materialization_timestamp,
        )
    elif asset_freshness_health_state.freshness_state == FreshnessState.UNKNOWN:
        return GrapheneAssetHealthStatus.UNKNOWN, None
    elif asset_freshness_health_state.freshness_state == FreshnessState.NOT_APPLICABLE:
        return GrapheneAssetHealthStatus.NOT_APPLICABLE, None

    else:
        check.failed(f"Unexpected freshness state: {asset_freshness_health_state.freshness_state}")


async def get_materialization_status_and_metadata(
    graphene_info: "ResolveInfo", asset_key: AssetKey
) -> tuple[str, Optional["GrapheneAssetHealthMaterializationMeta"]]:
    """Gets an AssetMaterializationHealthState object for an asset, either via streamline or by computing
    it based on the state of the DB. Then converts it to a GrapheneAssetHealthStatus and the metadata
    needed to power the UIs. Metadata is fetched from the AssetLatestMaterializationState object, again
    either via streamline or by computing it based on the state of the DB.
    """
    from dagster_graphql.schema.asset_health import (
        GrapheneAssetHealthMaterializationDegradedNotPartitionedMeta,
        GrapheneAssetHealthMaterializationDegradedPartitionedMeta,
        GrapheneAssetHealthMaterializationHealthyPartitionedMeta,
        GrapheneAssetHealthStatus,
    )

    asset_materialization_health_state = None
    if graphene_info.context.instance.streamline_read_asset_health_supported():
        asset_materialization_health_state = (
            graphene_info.context.instance.get_asset_materialization_health_state_for_asset(
                asset_key
            )
        )
    # captures streamline disabled or consumer state doesn't exist (because it's an observable source asset)
    if asset_materialization_health_state is None:
        node_snap = graphene_info.context.asset_graph.get(asset_key)
        if node_snap.is_observable and not node_snap.is_materializable:  # observable source asset
            # get the asset record to see if there is an observation event
            asset_record = await AssetRecord.gen(graphene_info.context, asset_key)
            if asset_record and asset_record.asset_entry.last_observation is not None:
                return GrapheneAssetHealthStatus.HEALTHY, None
            return GrapheneAssetHealthStatus.UNKNOWN, None

        asset_materialization_health_state = (
            await AssetMaterializationHealthState.compute_for_asset(
                asset_key,
                node_snap.partitions_def,
                graphene_info.context,
            )
        )

    if asset_materialization_health_state.health_status == AssetHealthStatus.HEALTHY:
        num_missing = 0
        total_num_partitions = 0
        if asset_materialization_health_state.partitions_def is not None:
            total_num_partitions = (
                asset_materialization_health_state.partitions_def.get_num_partitions(
                    dynamic_partitions_store=graphene_info.context.instance
                )
            )
            # asset is health, so no partitions are failed
            num_materialized = len(
                asset_materialization_health_state.materialized_subset.subset_value
            )
            num_missing = total_num_partitions - num_materialized
        if num_missing > 0 and total_num_partitions > 0:
            meta = GrapheneAssetHealthMaterializationHealthyPartitionedMeta(
                numMissingPartitions=num_missing,
                totalNumPartitions=total_num_partitions,
            )
        else:
            # captures the case when asset is not partitioned, or the asset is partitioned and all partitions are materialized
            meta = None
        return GrapheneAssetHealthStatus.HEALTHY, meta
    elif asset_materialization_health_state.health_status == AssetHealthStatus.DEGRADED:
        if asset_materialization_health_state.partitions_def is not None:
            total_num_partitions = (
                asset_materialization_health_state.partitions_def.get_num_partitions(
                    dynamic_partitions_store=graphene_info.context.instance
                )
            )
            num_failed = len(asset_materialization_health_state.failed_subset.subset_value)
            num_materialized = len(
                asset_materialization_health_state.currently_materialized_subset.subset_value
            )
            num_missing = total_num_partitions - num_materialized - num_failed
            meta = GrapheneAssetHealthMaterializationDegradedPartitionedMeta(
                numFailedPartitions=num_failed,
                numMissingPartitions=num_missing,
                totalNumPartitions=total_num_partitions,
            )
        else:
            meta = GrapheneAssetHealthMaterializationDegradedNotPartitionedMeta(
                failedRunId=asset_materialization_health_state.latest_terminal_run_id,
            )
        return GrapheneAssetHealthStatus.DEGRADED, meta
    elif asset_materialization_health_state.health_status == AssetHealthStatus.UNKNOWN:
        return GrapheneAssetHealthStatus.UNKNOWN, None
    else:
        check.failed(
            f"Unexpected materialization health status: {asset_materialization_health_state.health_status}"
        )
