from collections.abc import Sequence
from typing import TYPE_CHECKING

from dagster._core.definitions.asset_check_spec import AssetCheckSeverity
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.remote_asset_graph import RemoteAssetCheckNode
from dagster._core.storage.asset_check_execution_record import AssetCheckExecutionResolvedStatus
from dagster._core.storage.event_log.base import AssetCheckSummaryRecord
from dagster._streamline.asset_check_health import AssetCheckHealthState
from dagster_shared.record import record

if TYPE_CHECKING:
    from dagster_graphql.schema.util import ResolveInfo


@record
class AssetChecksStatusCounts:
    num_passing: int
    num_warning: int
    num_failed: int
    num_unexecuted: int
    total_num: int


async def _compute_asset_check_status_counts(
    graphene_info: "ResolveInfo", asset_key: AssetKey
) -> AssetChecksStatusCounts:
    """Computes the number of asset checks in each terminal state for an asset so that the overall
    health can be computed in asset_check_health_status_and_metadata_from_counts. Does this by fetching the
    asset check summary record for each check and checking the status of the latest completed execution.
    """
    remote_check_nodes = graphene_info.context.asset_graph.get_checks_for_asset(asset_key)

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

    return AssetChecksStatusCounts(
        num_failed=num_failed,
        num_warning=num_warning,
        num_unexecuted=num_unexecuted_checks,
        total_num=total_num_checks,
        num_passing=num_passing,
    )


def _get_asset_check_status_counts_from_asset_health_state(
    asset_check_health_state: AssetCheckHealthState,
    remote_check_nodes: Sequence[RemoteAssetCheckNode],
) -> AssetChecksStatusCounts:
    """Converts the asset check health data from streamline into the shared AssetChecksStatusCounts object.

    When streamline starts maintaining the overall health for checks for the asset, we can remove this and
    directly return the state from the streamline object. But we need to be able to handle not-executed
    checks in streamline first.
    """
    total_num_checks = len(remote_check_nodes)
    num_failed = len(asset_check_health_state.failing_checks)
    num_warning = len(asset_check_health_state.warning_checks)
    num_passing = len(asset_check_health_state.passing_checks)

    return AssetChecksStatusCounts(
        num_failed=num_failed,
        num_warning=num_warning,
        num_unexecuted=total_num_checks - num_failed - num_warning - num_passing,
        total_num=total_num_checks,
        num_passing=num_passing,
    )


async def get_asset_check_status_counts(
    graphene_info: "ResolveInfo",
    asset_key: AssetKey,
    remote_check_nodes: Sequence[RemoteAssetCheckNode],
) -> AssetChecksStatusCounts:
    """Gets the number of asset checks in each terminal state for an asset so that the overall health
    for the asset can be computed. If streamline is enabled, use the data from streamline since it is a
    more performant query. Otherwise, compute the status counts from the data available in the db.
    """
    if graphene_info.context.instance.streamline_read_supported():
        asset_check_health_state = (
            graphene_info.context.instance.get_asset_check_health_state_for_asset(asset_key)
        )
        if asset_check_health_state is None:
            # asset_check_health_state_for is only None if no checks have been executed
            return AssetChecksStatusCounts(
                num_failed=0,
                num_warning=0,
                num_unexecuted=len(remote_check_nodes),
                total_num=len(remote_check_nodes),
                num_passing=0,
            )

        return _get_asset_check_status_counts_from_asset_health_state(
            asset_check_health_state, remote_check_nodes
        )
    # otherwise compute the status counts from scratch
    return await _compute_asset_check_status_counts(graphene_info, asset_key)
