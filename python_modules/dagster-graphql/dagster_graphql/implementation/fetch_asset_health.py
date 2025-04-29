from typing import TYPE_CHECKING, Optional

from dagster._core.definitions.asset_check_spec import AssetCheckSeverity
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.storage.asset_check_execution_record import AssetCheckExecutionResolvedStatus
from dagster._core.storage.event_log.base import AssetCheckSummaryRecord
from dagster._streamline.asset_check_health import AssetCheckHealthState
from dagster._streamline.asset_health import AssetHealthStatus

if TYPE_CHECKING:
    from dagster_graphql.schema.asset_health import GrapheneAssetHealthCheckMeta
    from dagster_graphql.schema.util import ResolveInfo


async def _compute_asset_check_health_state(
    graphene_info: "ResolveInfo", asset_key: AssetKey
) -> AssetCheckHealthState:
    """Computes the number of asset checks in each terminal state for an asset so that the overall
    health can be computed in get_asset_check_status_and_metadata. Does this by fetching the
    asset check summary record for each check and checking the status of the latest completed execution.
    """
    remote_check_nodes = graphene_info.context.asset_graph.get_checks_for_asset(asset_key)
    if not remote_check_nodes or len(remote_check_nodes) == 0:
        # asset doesn't have checks defined
        return AssetCheckHealthState.default()

    failed_checks = set()
    warning_checks = set()
    passing_checks = set()
    asset_check_summary_records = await AssetCheckSummaryRecord.gen_many(
        graphene_info.context,
        [remote_check_node.asset_check.key for remote_check_node in remote_check_nodes],
    )
    for summary_record in asset_check_summary_records:
        if summary_record is None or summary_record.last_check_execution_record is None:
            # the check has never been executed.
            continue

        # if the last_check_execution_record is completed, it will be the same as last_completed_check_execution_record,
        # but we check the last_check_execution_record status first since there is an edge case
        # where the record will have status PLANNED, but the resolve_status will be EXECUTION_FAILED
        # because the run for the check failed.
        last_check_execution_status = (
            await summary_record.last_check_execution_record.resolve_status(graphene_info.context)
        )
        last_check_evaluation = summary_record.last_check_execution_record.evaluation

        if last_check_execution_status in [
            AssetCheckExecutionResolvedStatus.IN_PROGRESS,
            AssetCheckExecutionResolvedStatus.SKIPPED,
        ]:
            # the last check is still in progress or is skipped, so we want to check the status of
            # the latest completed check instead
            if summary_record.last_completed_check_execution_record is None:
                # the check hasn't been executed prior to this in progress check
                continue
            last_check_execution_status = (
                await summary_record.last_completed_check_execution_record.resolve_status(
                    graphene_info.context
                )
            )
            last_check_evaluation = summary_record.last_completed_check_execution_record.evaluation

        if last_check_execution_status == AssetCheckExecutionResolvedStatus.FAILED:
            # failed checks should always have an evaluation, but default to ERROR if not
            if last_check_evaluation and last_check_evaluation.severity == AssetCheckSeverity.WARN:
                warning_checks.add(summary_record.asset_check_key)
            else:
                failed_checks.add(summary_record.asset_check_key)
        elif last_check_execution_status == AssetCheckExecutionResolvedStatus.EXECUTION_FAILED:
            # EXECUTION_FAILED checks may not have an evaluation, and we want to show these as
            # degraded health anyway.
            failed_checks.add(summary_record.asset_check_key)
        else:
            # asset check passed
            passing_checks.add(summary_record.asset_check_key)

    return AssetCheckHealthState(
        passing_checks=passing_checks,
        failing_checks=failed_checks,
        warning_checks=warning_checks,
        all_checks={node.asset_check.key for node in remote_check_nodes},
    )


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
        asset_check_health_state = await _compute_asset_check_health_state(graphene_info, asset_key)

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
                numUnexecutedChecks=len(asset_check_health_state.all_checks)
                - len(asset_check_health_state.passing_checks)
                - len(asset_check_health_state.failing_checks)
                - len(asset_check_health_state.warning_checks),
                totalNumChecks=len(asset_check_health_state.all_checks),
            ),
        )
    else:  # asset_check_health_state.health_status == AssetHealthStatus.NOT_APPLICABLE
        return GrapheneAssetHealthStatus.NOT_APPLICABLE, None
