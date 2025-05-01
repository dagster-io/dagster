from typing import TYPE_CHECKING, Optional

import dagster._check as check
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.freshness import FreshnessState
from dagster._streamline.asset_check_health import AssetCheckHealthState
from dagster._streamline.asset_freshness_health import AssetFreshnessHealthState
from dagster._streamline.asset_health import AssetHealthStatus

if TYPE_CHECKING:
    from dagster_graphql.schema.asset_health import (
        GrapheneAssetHealthCheckMeta,
        GrapheneAssetHealthFreshnessMeta,
    )
    from dagster_graphql.schema.util import ResolveInfo


async def get_asset_check_status_and_metadata(
    graphene_info: "ResolveInfo",
    asset_key: AssetKey,
) -> tuple[str, Optional["GrapheneAssetHealthCheckMeta"]]:
    """Converts an AssetCheckHealthState object to a GrapheneAssetHealthStatus and the metdata
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
    it based on the state of the DB. Then converts it to a GrapheneAssetHealthStatus and the metdata
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
        return GrapheneAssetHealthStatus.HEALTHY, None
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
