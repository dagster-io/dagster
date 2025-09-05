from collections.abc import Iterable
from typing import TYPE_CHECKING, Optional, Union

from dagster_shared import record
from dagster_shared.serdes import whitelist_for_serdes

import dagster._check as check
from dagster._core.definitions.asset_checks.asset_check_spec import AssetCheckSeverity
from dagster._core.definitions.asset_health.asset_health import AssetHealthStatus
from dagster._core.definitions.asset_key import AssetCheckKey, AssetKey
from dagster._core.loader import LoadableBy, LoadingContext

if TYPE_CHECKING:
    from dagster._core.workspace.context import BaseWorkspaceRequestContext


@whitelist_for_serdes
@record.record
class AssetCheckHealthState(LoadableBy[AssetKey]):
    """Maintains a list of asset checks for the asset in each terminal state. If a check is in progress,
    it will not move to a new list until the execution is complete.
    """

    passing_checks: set[AssetCheckKey]
    failing_checks: set[AssetCheckKey]
    warning_checks: set[AssetCheckKey]
    all_checks: set[AssetCheckKey]

    @classmethod
    def default(cls) -> "AssetCheckHealthState":
        return cls(
            passing_checks=set(),
            failing_checks=set(),
            warning_checks=set(),
            all_checks=set(),
        )

    @property
    def health_status(self) -> AssetHealthStatus:
        """Returns the health status of the asset based on the checks."""
        if len(self.all_checks) == 0:
            return AssetHealthStatus.NOT_APPLICABLE
        if len(self.failing_checks) > 0:
            return AssetHealthStatus.DEGRADED
        if len(self.warning_checks) > 0:
            return AssetHealthStatus.WARNING

        num_unexecuted = (
            len(self.all_checks)
            - len(self.passing_checks)
            - len(self.failing_checks)
            - len(self.warning_checks)
        )
        if num_unexecuted > 0:
            return AssetHealthStatus.UNKNOWN
        # all checks are passing
        return AssetHealthStatus.HEALTHY

    @classmethod
    async def compute_for_asset_checks(
        cls, check_keys: set[AssetCheckKey], loading_context: LoadingContext
    ) -> "AssetCheckHealthState":
        """Using the latest terminal state for each check as stored in the DB, returns a set of
        asset checks in each terminal state. If a check is in progress, it remains in the terminal
        state it was in prior to the in progress execution.
        """
        from dagster._core.storage.asset_check_execution_record import (
            AssetCheckExecutionResolvedStatus,
        )
        from dagster._core.storage.event_log.base import AssetCheckSummaryRecord

        if len(check_keys) == 0:
            # no checks defined
            return AssetCheckHealthState.default()

        passing_checks = set()
        warning_checks = set()
        failing_checks = set()

        check_records = await AssetCheckSummaryRecord.gen_many(
            loading_context,
            check_keys,
        )

        for check_record in check_records:
            if check_record is None or check_record.last_check_execution_record is None:
                # check has never been executed
                continue

            check_key = check_record.asset_check_key

            # if the last_check_execution_record is completed, it will be the same as last_completed_check_execution_record,
            # but we check the last_check_execution_record status first since there is an edge case
            # where the record will have status PLANNED, but the resolve_status will be EXECUTION_FAILED
            # because the run for the check failed.
            last_check_execution_status = (
                await check_record.last_check_execution_record.resolve_status(loading_context)
            )
            last_check_evaluation = check_record.last_check_execution_record.evaluation

            if last_check_execution_status in [
                AssetCheckExecutionResolvedStatus.IN_PROGRESS,
                AssetCheckExecutionResolvedStatus.SKIPPED,
            ]:
                # the last check is still in progress or is skipped, so we want to check the status of
                # the latest completed check instead
                if check_record.last_completed_check_execution_record is None:
                    # the check hasn't been executed prior to this in progress check
                    continue
                # should never need to fetch a run since the non-resolved status is success or failed.
                # this method converts directly to the resolved status
                last_check_execution_status = (
                    await check_record.last_completed_check_execution_record.resolve_status(
                        loading_context
                    )
                )
                last_check_evaluation = (
                    check_record.last_completed_check_execution_record.evaluation
                )

            if last_check_execution_status == AssetCheckExecutionResolvedStatus.FAILED:
                # failed checks should always have an evaluation, but default to ERROR if not
                if (
                    last_check_evaluation
                    and last_check_evaluation.severity == AssetCheckSeverity.WARN
                ):
                    warning_checks.add(check_key)
                else:
                    failing_checks.add(check_key)
            elif last_check_execution_status == AssetCheckExecutionResolvedStatus.EXECUTION_FAILED:
                # EXECUTION_FAILED checks don't have an evaluation and we want to report them as failures
                failing_checks.add(check_key)
            else:
                # asset check passed
                passing_checks.add(check_key)

        return AssetCheckHealthState(
            passing_checks=passing_checks,
            failing_checks=failing_checks,
            warning_checks=warning_checks,
            all_checks=check_keys,
        )

    @classmethod
    def _blocking_batch_load(
        cls, keys: Iterable[AssetKey], context: LoadingContext
    ) -> Iterable[Optional["AssetCheckHealthState"]]:
        asset_check_health_states = context.instance.get_asset_check_health_state_for_assets(
            list(keys)
        )
        return [asset_check_health_states.get(key) for key in keys]


@whitelist_for_serdes
@record.record
class AssetHealthCheckDegradedMetadata:
    num_failed_checks: int
    num_warning_checks: int
    total_num_checks: int


@whitelist_for_serdes
@record.record
class AssetHealthCheckWarningMetadata:
    num_warning_checks: int
    total_num_checks: int


@whitelist_for_serdes
@record.record
class AssetHealthCheckUnknownMetadata:
    num_not_executed_checks: int
    total_num_checks: int


AssetHealthCheckMetadata = Union[
    AssetHealthCheckDegradedMetadata,
    AssetHealthCheckWarningMetadata,
    AssetHealthCheckUnknownMetadata,
]


async def get_asset_check_status_and_metadata(
    context: "BaseWorkspaceRequestContext",
    asset_key: AssetKey,
) -> tuple[AssetHealthStatus, Optional["AssetHealthCheckMetadata"]]:
    """Converts an AssetCheckHealthState object to a AssetHealthStatus and the metadata
    needed to power the UIs and alerting.
    """
    asset_check_health_state = await AssetCheckHealthState.gen(context, asset_key)
    # captures streamline disabled or consumer state doesn't exist
    if asset_check_health_state is None:
        if context.instance.streamline_read_asset_health_required("asset-check-health"):
            return AssetHealthStatus.UNKNOWN, None

        # Note - this will only compute check health if there is a definition for the asset and checks in the
        # asset graph. If check results are reported for assets or checks that are not in the asset graph, those
        # results will not be picked up. If we add storage methods to get all check results for an asset by
        # asset key, rather than by check keys, we could compute check health for the asset in this case.

        if not context.asset_graph.has(
            asset_key
        ) or not context.asset_graph.get_check_keys_for_assets({asset_key}):
            return AssetHealthStatus.NOT_APPLICABLE, None

        remote_check_nodes = context.asset_graph.get_checks_for_asset(asset_key)
        asset_check_health_state = await AssetCheckHealthState.compute_for_asset_checks(
            {remote_check_node.asset_check.key for remote_check_node in remote_check_nodes},
            context,
        )

    if asset_check_health_state.health_status == AssetHealthStatus.HEALTHY:
        return AssetHealthStatus.HEALTHY, None
    if asset_check_health_state.health_status == AssetHealthStatus.WARNING:
        return (
            AssetHealthStatus.WARNING,
            AssetHealthCheckWarningMetadata(
                num_warning_checks=len(asset_check_health_state.warning_checks),
                total_num_checks=len(asset_check_health_state.all_checks),
            ),
        )
    if asset_check_health_state.health_status == AssetHealthStatus.DEGRADED:
        return (
            AssetHealthStatus.DEGRADED,
            AssetHealthCheckDegradedMetadata(
                num_failed_checks=len(asset_check_health_state.failing_checks),
                num_warning_checks=len(asset_check_health_state.warning_checks),
                total_num_checks=len(asset_check_health_state.all_checks),
            ),
        )
    if asset_check_health_state.health_status == AssetHealthStatus.UNKNOWN:
        return (
            AssetHealthStatus.UNKNOWN,
            AssetHealthCheckUnknownMetadata(
                num_not_executed_checks=len(asset_check_health_state.all_checks)
                - len(asset_check_health_state.passing_checks)
                - len(asset_check_health_state.failing_checks)
                - len(asset_check_health_state.warning_checks),
                total_num_checks=len(asset_check_health_state.all_checks),
            ),
        )
    elif asset_check_health_state.health_status == AssetHealthStatus.NOT_APPLICABLE:
        return AssetHealthStatus.NOT_APPLICABLE, None
    else:
        check.failed(
            f"Unexpected asset check health status: {asset_check_health_state.health_status}"
        )
