from typing import TYPE_CHECKING, List, Optional, Union

import dagster._check as check
from dagster import AssetKey
from dagster._core.host_representation.external_data import ExternalAssetCheck
from dagster._core.instance import DagsterInstance
from dagster._core.storage.asset_check_execution_record import (
    AssetCheckExecutionRecord,
    AssetCheckExecutionRecordStatus,
    AssetCheckExecutionResolvedStatus,
)
from dagster._core.storage.dagster_run import DagsterRunStatus

from ..schema.asset_checks import (
    GrapheneAssetCheck,
    GrapheneAssetCheckExecution,
    GrapheneAssetCheckNeedsMigrationError,
    GrapheneAssetChecks,
)

if TYPE_CHECKING:
    from ..schema.util import ResolveInfo


def _fetch_asset_checks(
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


def has_asset_checks(
    graphene_info: "ResolveInfo",
    asset_key: AssetKey,
) -> bool:
    return bool(_fetch_asset_checks(graphene_info, asset_key).checks)


def fetch_asset_checks(
    graphene_info: "ResolveInfo",
    asset_key: AssetKey,
    check_name: Optional[str] = None,
) -> Union[GrapheneAssetCheckNeedsMigrationError, GrapheneAssetChecks]:
    if not graphene_info.context.instance.event_log_storage.supports_asset_checks:
        return GrapheneAssetCheckNeedsMigrationError(
            message="Asset checks require an instance migration. Run `dagster instance migrate`."
        )
    return _fetch_asset_checks(graphene_info, asset_key, check_name)


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


def fetch_executions(
    instance: DagsterInstance, asset_check: ExternalAssetCheck, limit: int, cursor: Optional[str]
) -> List[GrapheneAssetCheckExecution]:
    executions = instance.event_log_storage.get_asset_check_executions(
        asset_key=asset_check.asset_key,
        check_name=asset_check.name,
        limit=limit,
        cursor=int(cursor) if cursor else None,
    )

    res = []
    for execution in executions:
        resolved_status = _get_asset_check_execution_status(instance, execution)
        res.append(GrapheneAssetCheckExecution(execution, resolved_status))

    return res
