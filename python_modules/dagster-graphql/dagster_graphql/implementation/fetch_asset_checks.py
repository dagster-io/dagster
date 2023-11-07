from typing import TYPE_CHECKING, Iterator, List, Mapping, Optional, Sequence, Tuple

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
from dagster._core.storage.dagster_run import DagsterRunStatus, RunsFilter
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


# fetch all statuses at once in order to batch the run query
def get_asset_check_execution_statuses_by_id(
    instance: DagsterInstance, executions: Sequence[AssetCheckExecutionRecord]
) -> Mapping[int, AssetCheckExecutionResolvedStatus]:
    planned_status_executions = [
        e for e in executions if e.status == AssetCheckExecutionRecordStatus.PLANNED
    ]
    if planned_status_executions:
        planned_status_run_ids = list({e.run_id for e in planned_status_executions})
        planned_execution_runs_by_run_id = {
            r.run_id: r
            for r in instance.get_runs(filters=RunsFilter(run_ids=planned_status_run_ids))
        }
    else:
        planned_execution_runs_by_run_id = {}

    def _status_for_execution(
        execution: AssetCheckExecutionRecord
    ) -> AssetCheckExecutionResolvedStatus:
        record_status = execution.status

        if record_status == AssetCheckExecutionRecordStatus.SUCCEEDED:
            return AssetCheckExecutionResolvedStatus.SUCCEEDED
        elif record_status == AssetCheckExecutionRecordStatus.FAILED:
            return AssetCheckExecutionResolvedStatus.FAILED
        # Asset checks stay in PLANNED status until the evaluation event arrives. Check if the run is
        # still active, and if not, return the actual status.
        elif record_status == AssetCheckExecutionRecordStatus.PLANNED:
            check.invariant(
                execution.run_id in planned_execution_runs_by_run_id, "Check run not found"
            )
            run = planned_execution_runs_by_run_id[execution.run_id]

            if run.is_finished:
                if run.status == DagsterRunStatus.FAILURE:
                    return AssetCheckExecutionResolvedStatus.EXECUTION_FAILED
                else:
                    return AssetCheckExecutionResolvedStatus.SKIPPED
            else:
                return AssetCheckExecutionResolvedStatus.IN_PROGRESS

        else:
            check.failed(f"Unexpected status {record_status}")

    return {e.id: _status_for_execution(e) for e in executions}


def fetch_asset_check_executions(
    instance: DagsterInstance, asset_check_key: AssetCheckKey, limit: int, cursor: Optional[str]
) -> List[GrapheneAssetCheckExecution]:
    executions = instance.event_log_storage.get_asset_check_execution_history(
        check_key=asset_check_key,
        limit=limit,
        cursor=int(cursor) if cursor else None,
    )
    statuses = get_asset_check_execution_statuses_by_id(instance, executions)

    res = []
    for execution in executions:
        res.append(GrapheneAssetCheckExecution(execution, statuses[execution.id]))

    return res
