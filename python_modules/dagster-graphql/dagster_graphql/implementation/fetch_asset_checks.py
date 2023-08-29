from typing import TYPE_CHECKING, List, Optional

import dagster._check as check
from dagster import AssetKey
from dagster._core.host_representation.external_data import ExternalAssetCheck
from dagster._core.instance import DagsterInstance
from dagster._core.storage.asset_check_execution_record import (
    AssetCheckExecutionRecord,
    AssetCheckExecutionResolvedStatus,
    AssetCheckExecutionStoredStatus,
)
from dagster._core.storage.dagster_run import DagsterRunStatus

from ..schema.asset_checks import (
    GrapheneAssetCheck,
    GrapheneAssetCheckExecution,
    GrapheneAssetChecks,
)

if TYPE_CHECKING:
    from ..schema.util import ResolveInfo


def fetch_asset_checks(
    graphene_info: "ResolveInfo",
    asset_key: AssetKey,
    check_name: Optional[str] = None,
) -> GrapheneAssetChecks:
    external_asset_checks = []
    for location in graphene_info.context.code_locations:
        for repository in location.get_repositories().values():
            for external_check in repository.external_repository_data.external_asset_checks or []:
                if external_check.asset_key == asset_key:
                    if not check_name or check_name == external_check.name:
                        external_asset_checks.append(external_check)

    return GrapheneAssetChecks(
        checks=[GrapheneAssetCheck(check) for check in external_asset_checks]
    )


def _get_asset_check_execution_status(
    instance: DagsterInstance, execution: AssetCheckExecutionRecord
) -> AssetCheckExecutionResolvedStatus:
    """Asset checks stay in PLANNED status until the evaluation event arives. Check if the run is
    still active, and if not, return the actual status.
    """
    stored_status = execution.stored_status

    if stored_status == AssetCheckExecutionStoredStatus.SUCCESS:
        return AssetCheckExecutionResolvedStatus.SUCCESS
    elif stored_status == AssetCheckExecutionStoredStatus.FAILURE:
        return AssetCheckExecutionResolvedStatus.FAILURE
    elif stored_status == AssetCheckExecutionStoredStatus.PLANNED:
        run = check.not_none(instance.get_run_by_id(execution.run_id))

        if run.is_finished:
            if run.status == DagsterRunStatus.FAILURE:
                return AssetCheckExecutionResolvedStatus.EXECUTION_FAILURE
            else:
                return AssetCheckExecutionResolvedStatus.SKIPPED
        else:
            return AssetCheckExecutionResolvedStatus.IN_PROGRESS

    else:
        check.failed(f"Unexpected status {stored_status}")


def _get_targets_latest_materialization(
    instance: DagsterInstance,
    external_asset_check: ExternalAssetCheck,
    execution: AssetCheckExecutionRecord,
    resolved_status: AssetCheckExecutionResolvedStatus,
) -> bool:
    if resolved_status == AssetCheckExecutionResolvedStatus.IN_PROGRESS:
        # always assume that an in progress check will target the latest materialization
        return True
    else:
        records = instance.get_asset_records([external_asset_check.asset_key])
        latest_materialization = (
            records[0].asset_entry.last_materialization_record if records else None
        )

        if not latest_materialization:
            # asset hasn't been materialized yet, so no need to hide the check
            return True

        latest_materialization_run_id = latest_materialization.event_log_entry.run_id
        if latest_materialization_run_id == execution.run_id:
            return True

        latest_materialization_run_record = instance.get_run_record_by_id(
            latest_materialization_run_id
        )
        execution_run_record = instance.get_run_record_by_id(execution.run_id)

        if execution_run_record.start_time > latest_materialization_run_record.start_time:
            return True

        return False


def fetch_executions(
    instance: DagsterInstance,
    external_asset_check: ExternalAssetCheck,
    limit: int,
    cursor: Optional[str],
) -> List[GrapheneAssetCheckExecution]:
    executions = instance.event_log_storage.get_asset_check_executions(
        asset_key=external_asset_check.asset_key,
        check_name=external_asset_check.name,
        limit=limit,
        cursor=int(cursor) if cursor else None,
    )

    res = []
    for execution in executions:
        resolved_status = _get_asset_check_execution_status(instance, execution)

        res.append(GrapheneAssetCheckExecution(execution, resolved_status))

    return res
