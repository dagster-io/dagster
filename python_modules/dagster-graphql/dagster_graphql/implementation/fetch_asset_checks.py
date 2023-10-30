from typing import TYPE_CHECKING, List, Optional, cast

import dagster._check as check
from dagster import AssetKey
from dagster._core.definitions.asset_check_evaluation import AssetCheckEvaluation
from dagster._core.definitions.asset_check_spec import AssetCheckKey
from dagster._core.host_representation.external_data import ExternalAssetCheck
from dagster._core.instance import DagsterInstance
from dagster._core.storage.asset_check_execution_record import (
    AssetCheckExecutionRecord,
    AssetCheckExecutionRecordStatus,
    AssetCheckExecutionResolvedStatus,
)
from dagster._core.storage.dagster_run import DagsterRunStatus

from ..schema.asset_checks import (
    AssetChecksOrErrorUnion,
    GrapheneAssetCheckExecution,
    GrapheneAssetChecks,
)
from .asset_checks_loader import AssetChecksLoader, asset_checks_iter

if TYPE_CHECKING:
    from ..schema.util import ResolveInfo


def has_asset_checks(
    graphene_info: "ResolveInfo",
    asset_key: AssetKey,
) -> bool:
    return any(
        external_check.asset_key == asset_key
        for _, _, external_check in asset_checks_iter(graphene_info.context)
    )


def fetch_asset_checks(
    graphene_info: "ResolveInfo",
    asset_key: AssetKey,
    check_name: Optional[str] = None,
) -> AssetChecksOrErrorUnion:
    # use the batched loader with a single asset
    loader = AssetChecksLoader(context=graphene_info.context, asset_keys=[asset_key])
    all_checks = loader.get_checks_for_asset(asset_key)
    if not check_name or not isinstance(all_checks, GrapheneAssetChecks):
        return all_checks
    # the only case where we filter by check name is for execution history. We'll make that it's own resolver.
    # For now, just filter the checks in the response.
    return GrapheneAssetChecks(
        checks=[check for check in all_checks.checks if check._asset_check.name == check_name]  # noqa: SLF001
    )


def _get_asset_check_execution_status(
    instance: DagsterInstance, execution: AssetCheckExecutionRecord
) -> AssetCheckExecutionResolvedStatus:
    """Asset checks stay in PLANNED status until the evaluation event arives. Check if the run is
    still active, and if not, return the actual status.
    """
    record_status = execution.status

    if record_status == AssetCheckExecutionRecordStatus.SUCCEEDED:
        return AssetCheckExecutionResolvedStatus.SUCCEEDED
    elif record_status == AssetCheckExecutionRecordStatus.FAILED:
        return AssetCheckExecutionResolvedStatus.FAILED
    elif record_status == AssetCheckExecutionRecordStatus.PLANNED:
        run = check.not_none(instance.get_run_by_id(execution.run_id))

        if run.is_finished:
            if run.status == DagsterRunStatus.FAILURE:
                return AssetCheckExecutionResolvedStatus.EXECUTION_FAILED
            else:
                return AssetCheckExecutionResolvedStatus.SKIPPED
        else:
            return AssetCheckExecutionResolvedStatus.IN_PROGRESS

    else:
        check.failed(f"Unexpected status {record_status}")


def fetch_asset_check_executions(
    instance: DagsterInstance, asset_check_key: AssetCheckKey, limit: int, cursor: Optional[str]
) -> List[GrapheneAssetCheckExecution]:
    executions = instance.event_log_storage.get_asset_check_execution_history(
        check_key=asset_check_key,
        limit=limit,
        cursor=int(cursor) if cursor else None,
    )

    res = []
    for execution in executions:
        resolved_status = _get_asset_check_execution_status(instance, execution)
        res.append(GrapheneAssetCheckExecution(execution, resolved_status))

    return res


def _execution_targets_latest_materialization(
    instance: DagsterInstance,
    external_asset_check: ExternalAssetCheck,
    execution: AssetCheckExecutionRecord,
    resolved_status: AssetCheckExecutionResolvedStatus,
) -> bool:
    # always show in progress checks
    if resolved_status == AssetCheckExecutionResolvedStatus.IN_PROGRESS:
        return True

    records = instance.get_asset_records([external_asset_check.asset_key])
    latest_materialization = records[0].asset_entry.last_materialization_record if records else None

    if not latest_materialization:
        # asset hasn't been materialized yet, so no reason to hide the check
        return True

    # If the check is executed in the same run as the materialization, then show it.
    # This is a workaround to support the 'stage then promote' graph asset pattern,
    # where checks happen before a materialization.
    latest_materialization_run_id = latest_materialization.event_log_entry.run_id
    if latest_materialization_run_id == execution.run_id:
        return True

    if resolved_status in [
        AssetCheckExecutionResolvedStatus.SUCCEEDED,
        AssetCheckExecutionResolvedStatus.FAILED,
    ]:
        evaluation = cast(
            AssetCheckEvaluation,
            check.not_none(check.not_none(execution.event).dagster_event).event_specific_data,
        )
        if not evaluation.target_materialization_data:
            # check ran before the materialization was created
            return False

        # if the check matches the latest materialization, then show it
        return (
            evaluation.target_materialization_data.storage_id == latest_materialization.storage_id
        )

    # in this case the evaluation didn't complete, so we don't have target_materialization_data
    elif resolved_status in [
        AssetCheckExecutionResolvedStatus.EXECUTION_FAILED,
        AssetCheckExecutionResolvedStatus.SKIPPED,
    ]:
        # As a last ditch effort, check if the check's run was launched after the materialization's
        latest_materialization_run_record = instance.get_run_record_by_id(
            latest_materialization_run_id
        )
        execution_run_record = instance.get_run_record_by_id(execution.run_id)
        return bool(
            latest_materialization_run_record
            and execution_run_record
            and execution_run_record.create_timestamp
            > latest_materialization_run_record.create_timestamp
        )

    else:
        check.failed(f"Unexpected check status {resolved_status}")


def fetch_execution_for_latest_materialization(
    instance: DagsterInstance, external_asset_check: ExternalAssetCheck
) -> Optional[GrapheneAssetCheckExecution]:
    # we hide executions if they aren't for the latest asset materialization.
    # currently we only consider the most recently launched check.

    executions = instance.event_log_storage.get_asset_check_execution_history(
        check_key=external_asset_check.key,
        limit=1,
        cursor=None,
    )
    if not executions:
        return None

    execution = executions[0]
    resolved_status = _get_asset_check_execution_status(instance, execution)

    return (
        GrapheneAssetCheckExecution(execution, resolved_status)
        if _execution_targets_latest_materialization(
            instance, external_asset_check, execution, resolved_status
        )
        else None
    )
