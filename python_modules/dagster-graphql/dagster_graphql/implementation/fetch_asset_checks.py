from typing import TYPE_CHECKING, Iterator, List, Optional, Tuple

import dagster._check as check
from dagster import AssetKey
from dagster._core.definitions.asset_check_spec import AssetCheckKey
from dagster._core.host_representation.code_location import CodeLocation
from dagster._core.host_representation.external import ExternalRepository
from dagster._core.host_representation.external_data import ExternalAssetCheck
from dagster._core.instance import DagsterInstance
from dagster._core.storage.asset_check_execution_record import (
    AssetCheckExecutionRecord,
    AssetCheckExecutionRecordStatus,
    AssetCheckExecutionResolvedStatus,
)
from dagster._core.storage.dagster_run import DagsterRunStatus
from dagster._core.workspace.context import WorkspaceRequestContext

from ..schema.asset_checks import (
    GrapheneAssetCheckExecution,
)
from .fetch_assets import repository_iter

if TYPE_CHECKING:
    from ..schema.util import ResolveInfo


def asset_checks_iter(
    context: WorkspaceRequestContext
) -> Iterator[Tuple[CodeLocation, ExternalRepository, ExternalAssetCheck]]:
    for location, repository in repository_iter(context):
        for external_check in repository.external_repository_data.external_asset_checks or []:
            yield (location, repository, external_check)


def has_asset_checks(
    graphene_info: "ResolveInfo",
    asset_key: AssetKey,
) -> bool:
    return any(
        external_check.asset_key == asset_key
        for _, _, external_check in asset_checks_iter(graphene_info.context)
    )


def get_asset_check_execution_status(
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
        resolved_status = get_asset_check_execution_status(instance, execution)
        res.append(GrapheneAssetCheckExecution(execution, resolved_status))

    return res
