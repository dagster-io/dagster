from typing import TYPE_CHECKING, Optional

from dagster._core.definitions.asset_check_spec import AssetCheckSeverity
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.storage.asset_check_execution_record import AssetCheckExecutionResolvedStatus
from dagster._core.storage.event_log.base import AssetCheckSummaryRecord
from dagster._streamline.asset_health import AssetHealthStatus

if TYPE_CHECKING:
    from dagster_graphql.schema.asset_health import GrapheneAssetHealthCheckMeta
    from dagster_graphql.schema.util import ResolveInfo


async def _compute_asset_check_status_and_metadata(
    graphene_info: "ResolveInfo", asset_key: AssetKey
) -> tuple[str, Optional["GrapheneAssetHealthCheckMeta"]]:
    """Computes the number of asset checks in each terminal state for an asset so that the overall
    health can be computed in asset_check_health_status_and_metadata_from_counts. Does this by fetching the
    asset check summary record for each check and checking the status of the latest completed execution.
    """
    from dagster_graphql.schema.asset_health import (
        GrapheneAssetHealthCheckDegradedMeta,
        GrapheneAssetHealthCheckUnknownMeta,
        GrapheneAssetHealthCheckWarningMeta,
        GrapheneAssetHealthStatus,
    )

    remote_check_nodes = graphene_info.context.asset_graph.get_checks_for_asset(asset_key)
    if not remote_check_nodes or len(remote_check_nodes) == 0:
        # asset doesn't have checks defined
        return GrapheneAssetHealthStatus.NOT_APPLICABLE, None

    total_num_checks = len(remote_check_nodes)
    num_failed = 0
    num_warning = 0
    num_passing = 0
    num_unexecuted_checks = 0
    asset_check_summary_records = await AssetCheckSummaryRecord.gen_many(
        graphene_info.context,
        [remote_check_node.asset_check.key for remote_check_node in remote_check_nodes],
    )
    for summary_record in asset_check_summary_records:
        if summary_record is None or summary_record.last_check_execution_record is None:
            # the check has never been executed.
            num_unexecuted_checks += 1
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
                num_unexecuted_checks += 1
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
                num_warning += 1
            else:
                num_failed += 1
        elif last_check_execution_status == AssetCheckExecutionResolvedStatus.EXECUTION_FAILED:
            # EXECUTION_FAILED checks may not have an evaluation, and we want to show these as
            # degraded health anyway.
            num_failed += 1
        else:
            # asset check passed
            num_passing += 1

    if num_failed > 0:
        return GrapheneAssetHealthStatus.DEGRADED, GrapheneAssetHealthCheckDegradedMeta(
            numFailedChecks=num_failed,
            numWarningChecks=num_warning,
            totalNumChecks=total_num_checks,
        )
    if num_warning > 0:
        return GrapheneAssetHealthStatus.WARNING, GrapheneAssetHealthCheckWarningMeta(
            numWarningChecks=num_warning,
            totalNumChecks=total_num_checks,
        )
    if num_unexecuted_checks > 0:
        # if any check has never been executed, we report this as unknown, even if other checks
        # have passed
        return (
            GrapheneAssetHealthStatus.UNKNOWN,
            GrapheneAssetHealthCheckUnknownMeta(
                numNotExecutedChecks=num_unexecuted_checks,
                totalNumChecks=total_num_checks,
            ),
        )
    # all checks must have executed and passed
    return GrapheneAssetHealthStatus.HEALTHY, None


def _get_streamline_asset_check_health_and_metadata(
    graphene_info: "ResolveInfo",
    asset_key: AssetKey,
) -> tuple[str, Optional["GrapheneAssetHealthCheckMeta"]]:
    from dagster_graphql.schema.asset_health import (
        GrapheneAssetHealthCheckDegradedMeta,
        GrapheneAssetHealthCheckUnknownMeta,
        GrapheneAssetHealthCheckWarningMeta,
        GrapheneAssetHealthStatus,
    )

    asset_check_health_state = (
        graphene_info.context.instance.get_asset_check_health_state_for_asset(asset_key)
    )
    if asset_check_health_state is None:
        # asset_check_health_state_for is only None if no are defined on the asset
        return GrapheneAssetHealthStatus.NOT_APPLICABLE, None

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


async def get_asset_check_status_and_metadata(
    graphene_info: "ResolveInfo",
    asset_key: AssetKey,
) -> tuple[str, Optional["GrapheneAssetHealthCheckMeta"]]:
    if graphene_info.context.instance.streamline_read_asset_health_supported():
        return _get_streamline_asset_check_health_and_metadata(graphene_info, asset_key)
    return await _compute_asset_check_status_and_metadata(graphene_info, asset_key)
