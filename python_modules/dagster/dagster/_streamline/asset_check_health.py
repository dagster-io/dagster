from dagster_shared import record
from dagster_shared.serdes import whitelist_for_serdes

from dagster._core.definitions.asset_check_spec import AssetCheckSeverity
from dagster._core.definitions.asset_key import AssetCheckKey
from dagster._core.loader import LoadingContext
from dagster._streamline.asset_health import AssetHealthStatus


@whitelist_for_serdes
@record.record
class AssetCheckHealthState:
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
