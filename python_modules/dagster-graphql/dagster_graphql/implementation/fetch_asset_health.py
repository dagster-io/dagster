from typing import TYPE_CHECKING, Optional

from dagster._core.definitions.asset_key import AssetKey
from dagster._streamline.asset_check_health import AssetCheckHealthState
from dagster._streamline.asset_health import AssetHealthStatus

if TYPE_CHECKING:
    from dagster_graphql.schema.asset_health import GrapheneAssetHealthCheckMeta
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
    else:  # asset_check_health_state.health_status == AssetHealthStatus.NOT_APPLICABLE
        return GrapheneAssetHealthStatus.NOT_APPLICABLE, None
