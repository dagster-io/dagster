from typing import TYPE_CHECKING, List, Optional, Union, cast

import dagster._check as check
from dagster import AssetKey
from dagster._core.definitions.asset_check_evaluation import AssetCheckEvaluation
from dagster._core.definitions.external_asset_graph import ExternalAssetGraph
from dagster._core.host_representation.external_data import ExternalAssetCheck
from dagster._core.instance import DagsterInstance
from dagster._core.storage.asset_check_execution_record import (
    AssetCheckExecutionRecord,
    AssetCheckExecutionRecordStatus,
    AssetCheckExecutionResolvedStatus,
    AssetCheckInstanceSupport,
)
from dagster._core.storage.dagster_run import DagsterRunStatus
from packaging import version

from ..schema.asset_checks import (
    GrapheneAssetCheck,
    GrapheneAssetCheckCanExecuteIndividually,
    GrapheneAssetCheckExecution,
    GrapheneAssetCheckNeedsAgentUpgradeError,
    GrapheneAssetCheckNeedsMigrationError,
    GrapheneAssetCheckNeedsUserCodeUpgrade,
    GrapheneAssetChecks,
)

if TYPE_CHECKING:
    from ..schema.util import ResolveInfo


# def _fetch_asset_checks(
#     graphene_info: "ResolveInfo",
#     asset_key: AssetKey,
#     check_name: Optional[str] = None,
# ) -> GrapheneAssetChecks:
#     asset_graph = ExternalAssetGraph.from_workspace(graphene_info.context)

#     external_asset_checks = []
#     for location in graphene_info.context.code_locations:
#         for repository in location.get_repositories().values():
#             for external_check in repository.external_repository_data.external_asset_checks or []:
#                 if external_check.asset_key == asset_key:
#                     if not check_name or check_name == external_check.name:
#                         if (
#                             len(asset_graph.get_required_asset_and_check_keys(external_check.key))
#                             > 1
#                         ):
#                             can_execute_individually = (
#                                 GrapheneAssetCheckCanExecuteIndividually.REQUIRES_MATERIALIZATION
#                             )
#                         else:
#                             can_execute_individually = (
#                                 GrapheneAssetCheckCanExecuteIndividually.CAN_EXECUTE
#                             )

#                         external_asset_checks.append((external_check, can_execute_individually))

#     return GrapheneAssetChecks(
#         checks=[
#             GrapheneAssetCheck(asset_check=check, can_execute_individually=can_execute_individually)
#             for check, can_execute_individually in external_asset_checks
#         ]
#     )


def has_asset_checks(
    graphene_info: "ResolveInfo",
    asset_key: AssetKey,
) -> bool:
    for location in graphene_info.context.code_locations:
        for repository in location.get_repositories().values():
            for external_check in repository.external_repository_data.external_asset_checks or []:
                if external_check.asset_key == asset_key:
                    return True
    return False


def fetch_asset_checks(
    graphene_info: "ResolveInfo",
    asset_key: AssetKey,
    check_name: Optional[str] = None,
) -> Union[
    GrapheneAssetCheckNeedsMigrationError,
    GrapheneAssetCheckNeedsUserCodeUpgrade,
    GrapheneAssetCheckNeedsAgentUpgradeError,
    GrapheneAssetChecks,
]:
    asset_check_support = graphene_info.context.instance.get_asset_check_support()
    if asset_check_support == AssetCheckInstanceSupport.NEEDS_MIGRATION:
        return GrapheneAssetCheckNeedsMigrationError(
            message="Asset checks require an instance migration. Run `dagster instance migrate`."
        )
    elif asset_check_support == AssetCheckInstanceSupport.NEEDS_AGENT_UPGRADE:
        return GrapheneAssetCheckNeedsAgentUpgradeError(
            "Asset checks require an agent upgrade to 1.5.0 or greater."
        )
    else:
        check.invariant(
            asset_check_support == AssetCheckInstanceSupport.SUPPORTED,
            f"Unexpected asset check support status {asset_check_support}",
        )

    external_asset_checks = []
    for location in graphene_info.context.code_locations:
        for repository in location.get_repositories().values():
            for external_check in repository.external_repository_data.external_asset_checks or []:
                if external_check.asset_key == asset_key:
                    if not check_name or check_name == external_check.name:
                        # check if the code location is too old to support executing asset checks individually
                        code_location_version = (location.get_dagster_library_versions() or {}).get(
                            "dagster"
                        )
                        if code_location_version and version.parse(
                            code_location_version
                        ) < version.parse("1.5"):
                            return GrapheneAssetCheckNeedsUserCodeUpgrade(
                                message=(
                                    "Asset checks require dagster>=1.5. Upgrade your dagster"
                                    " version for this code location."
                                )
                            )
                        external_asset_checks.append((external_check))

    asset_graph = ExternalAssetGraph.from_workspace(graphene_info.context)

    graphene_checks = []
    for external_check in external_asset_checks:
        can_execute_individually = (
            GrapheneAssetCheckCanExecuteIndividually.CAN_EXECUTE
            if len(asset_graph.get_required_asset_and_check_keys(external_check.key) or []) <= 1
            # NOTE: once we support multi checks, we'll need to add a case for
            # non subsettable multi checks
            else GrapheneAssetCheckCanExecuteIndividually.REQUIRES_MATERIALIZATION
        )
        graphene_checks.append(
            GrapheneAssetCheck(
                asset_check=external_check, can_execute_individually=can_execute_individually
            )
        )

    return GrapheneAssetChecks(checks=graphene_checks)


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
    executions = instance.event_log_storage.get_asset_check_execution_history(
        check_key=asset_check.key,
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
            check.not_none(
                check.not_none(execution.evaluation_event).dagster_event
            ).event_specific_data,
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
