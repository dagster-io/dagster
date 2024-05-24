from typing import Iterable, Iterator, List, Mapping, Optional, Tuple, cast

from dagster import (
    _check as check,
)
from dagster._core.definitions.asset_check_evaluation import AssetCheckEvaluation
from dagster._core.definitions.asset_check_spec import AssetCheckKey
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.selector import RepositorySelector
from dagster._core.instance import DagsterInstance
from dagster._core.remote_representation.code_location import CodeLocation
from dagster._core.remote_representation.external import ExternalRepository
from dagster._core.remote_representation.external_data import ExternalAssetCheck
from dagster._core.storage.asset_check_execution_record import (
    AssetCheckExecutionRecord,
    AssetCheckExecutionResolvedStatus,
    AssetCheckInstanceSupport,
)
from dagster._core.storage.event_log.base import AssetRecord
from dagster._core.workspace.context import WorkspaceRequestContext
from packaging import version

from dagster_graphql.schema.asset_checks import (
    AssetChecksOrErrorUnion,
    GrapheneAssetCheck,
    GrapheneAssetCheckCanExecuteIndividually,
    GrapheneAssetCheckNeedsAgentUpgradeError,
    GrapheneAssetCheckNeedsMigrationError,
    GrapheneAssetCheckNeedsUserCodeUpgrade,
    GrapheneAssetChecks,
)
from dagster_graphql.schema.inputs import GraphenePipelineSelector

from ..schema.asset_checks import (
    GrapheneAssetCheckExecution,
)
from .fetch_asset_checks import asset_checks_iter


class AssetChecksLoader:
    """A batch loader that fetches asset check definitions for a set of asset keys."""

    def __init__(self, context: WorkspaceRequestContext, asset_keys: Iterable[AssetKey]):
        self._context = context
        self._asset_keys = list(asset_keys)
        self._checks: Optional[Mapping[AssetKey, AssetChecksOrErrorUnion]] = None
        self._limit_per_asset = None
        self._pipeline = None

    def _get_external_checks(
        self, pipeline: Optional[GraphenePipelineSelector]
    ) -> Iterator[Tuple[CodeLocation, ExternalRepository, ExternalAssetCheck]]:
        if pipeline is None:
            yield from asset_checks_iter(self._context)
        else:
            job_name = cast(str, pipeline.pipelineName)
            repo_sel = RepositorySelector.from_graphql_input(pipeline)
            location = self._context.get_code_location(repo_sel.location_name)
            repo = location.get_repository(repo_sel.repository_name)
            external_asset_nodes = repo.get_external_asset_checks(job_name=job_name)
            for external_asset_node in external_asset_nodes:
                yield (location, repo, external_asset_node)

    def _fetch_checks(
        self, limit_per_asset: Optional[int], pipeline: Optional[GraphenePipelineSelector]
    ) -> Mapping[AssetKey, AssetChecksOrErrorUnion]:
        instance = self._context.instance
        asset_check_support = instance.get_asset_check_support()
        if asset_check_support == AssetCheckInstanceSupport.NEEDS_MIGRATION:
            return {
                asset_key: GrapheneAssetCheckNeedsMigrationError(
                    message="Asset checks require an instance migration. Run `dagster instance migrate`."
                )
                for asset_key in self._asset_keys
            }
        elif asset_check_support == AssetCheckInstanceSupport.NEEDS_AGENT_UPGRADE:
            return {
                asset_key: GrapheneAssetCheckNeedsAgentUpgradeError(
                    "Asset checks require an agent upgrade to 1.5.0 or greater."
                )
                for asset_key in self._asset_keys
            }
        else:
            check.invariant(
                asset_check_support == AssetCheckInstanceSupport.SUPPORTED,
                f"Unexpected asset check support status {asset_check_support}",
            )

        external_checks_by_asset_key: Mapping[AssetKey, List[ExternalAssetCheck]] = {}
        errors: Mapping[AssetKey, GrapheneAssetCheckNeedsUserCodeUpgrade] = {}

        for location, _, external_check in self._get_external_checks(pipeline=pipeline):
            if external_check.asset_key in self._asset_keys:
                # check if the code location is too old to support executing asset checks individually
                code_location_version = (location.get_dagster_library_versions() or {}).get(
                    "dagster"
                )
                if code_location_version and version.parse(code_location_version) < version.parse(
                    "1.5"
                ):
                    errors[external_check.asset_key] = GrapheneAssetCheckNeedsUserCodeUpgrade(
                        message=(
                            "Asset checks require dagster>=1.5. Upgrade your dagster"
                            " version for this code location."
                        )
                    )
                else:
                    external_checks_by_asset_key.setdefault(external_check.asset_key, []).append(
                        external_check
                    )

        if limit_per_asset:
            for asset_key, external_checks_for_asset in external_checks_by_asset_key.items():
                external_checks_by_asset_key[asset_key] = external_checks_for_asset[
                    :limit_per_asset
                ]

        all_check_keys = [
            external_check.key
            for external_checks in external_checks_by_asset_key.values()
            for external_check in external_checks
        ]
        execution_loader = AssetChecksExecutionForLatestMaterializationLoader(
            self._context.instance, check_keys=all_check_keys
        )

        asset_graph = self._context.asset_graph
        graphene_checks: Mapping[AssetKey, AssetChecksOrErrorUnion] = {}
        for asset_key in self._asset_keys:
            if asset_key in errors:
                graphene_checks[asset_key] = errors[asset_key]
            else:
                graphene_checks_for_asset = []
                for external_check in external_checks_by_asset_key.get(asset_key, []):
                    can_execute_individually = (
                        GrapheneAssetCheckCanExecuteIndividually.CAN_EXECUTE
                        if len(
                            asset_graph.get_execution_set_asset_and_check_keys(external_check.key)
                        )
                        <= 1
                        # NOTE: once we support multi checks, we'll need to add a case for
                        # non subsettable multi checks
                        else GrapheneAssetCheckCanExecuteIndividually.REQUIRES_MATERIALIZATION
                    )
                    graphene_checks_for_asset.append(
                        GrapheneAssetCheck(
                            asset_check=external_check,
                            can_execute_individually=can_execute_individually,
                            execution_loader=execution_loader,
                        )
                    )
                graphene_checks[asset_key] = GrapheneAssetChecks(checks=graphene_checks_for_asset)

        return graphene_checks

    def get_checks_for_asset(
        self,
        asset_key: AssetKey,
        limit: Optional[int] = None,
        pipeline: Optional[GraphenePipelineSelector] = None,
    ) -> AssetChecksOrErrorUnion:
        if self._checks is None:
            self._limit_per_asset = limit
            self._pipeline = pipeline
            self._checks = self._fetch_checks(limit_per_asset=limit, pipeline=pipeline)
        else:
            check.invariant(
                self._limit_per_asset == limit and self._pipeline == pipeline,
                "Limit and pipeline must be the same for all calls to this loader",
            )

        check.invariant(
            asset_key in self._checks, f"Asset key {asset_key} not included in this loader."
        )

        return self._checks[asset_key]


def _execution_targets_latest_materialization(
    instance: DagsterInstance,
    asset_record: Optional[AssetRecord],
    execution: AssetCheckExecutionRecord,
    resolved_status: AssetCheckExecutionResolvedStatus,
) -> bool:
    # always show in progress checks
    if resolved_status == AssetCheckExecutionResolvedStatus.IN_PROGRESS:
        return True

    latest_materialization = (
        asset_record.asset_entry.last_materialization_record if asset_record else None
    )

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


class AssetChecksExecutionForLatestMaterializationLoader:
    def __init__(self, instance: DagsterInstance, check_keys: List[AssetCheckKey]):
        self._instance = instance
        self._check_keys = check_keys
        self._executions: Optional[
            Mapping[AssetCheckKey, Optional[GrapheneAssetCheckExecution]]
        ] = None

    def _fetch_executions(self) -> Mapping[AssetCheckKey, Optional[GrapheneAssetCheckExecution]]:
        from .fetch_asset_checks import get_asset_check_execution_statuses_by_id

        latest_executions_by_check_key = (
            self._instance.event_log_storage.get_latest_asset_check_execution_by_key(
                self._check_keys
            )
        )
        statuses_by_execution_id = get_asset_check_execution_statuses_by_id(
            self._instance, list(latest_executions_by_check_key.values())
        )
        asset_records_by_asset_key = {
            record.asset_entry.asset_key: record
            for record in self._instance.get_asset_records(
                list({ck.asset_key for ck in self._check_keys})
            )
        }

        self._executions = {}
        for check_key in self._check_keys:
            execution = latest_executions_by_check_key.get(check_key)
            if not execution:
                self._executions[check_key] = None
            else:
                resolved_status = statuses_by_execution_id[execution.id]
                self._executions[check_key] = (
                    GrapheneAssetCheckExecution(execution, resolved_status)
                    if _execution_targets_latest_materialization(
                        instance=self._instance,
                        asset_record=asset_records_by_asset_key.get(check_key.asset_key),
                        execution=execution,
                        resolved_status=resolved_status,
                    )
                    else None
                )

        return self._executions

    def get_execution_for_latest_materialization(
        self, check_key: AssetCheckKey
    ) -> Optional[GrapheneAssetCheckExecution]:
        if self._executions is None:
            self._executions = self._fetch_executions()

        check.invariant(
            check_key in self._executions,
            f"Check key {check_key} not included in this loader.",
        )

        return self._executions[check_key]
