from typing import Optional

import pendulum

import dagster._check as check
from dagster._core.definitions.asset_daemon_context import AssetDaemonContext
from dagster._core.definitions.asset_daemon_cursor import AssetDaemonCursor
from dagster._core.definitions.external_asset_graph import ExternalAssetGraph
from dagster._core.definitions.run_request import RunRequest
from dagster._core.definitions.selector import JobSubsetSelector
from dagster._core.instance import DagsterInstance
from dagster._core.storage.dagster_run import DagsterRun, DagsterRunStatus
from dagster._core.storage.tags import (
    ASSET_EVALUATION_ID_TAG,
    AUTO_MATERIALIZE_TAG,
    AUTO_OBSERVE_TAG,
)
from dagster._core.workspace.context import IWorkspaceProcessContext
from dagster._core.workspace.workspace import IWorkspace
from dagster._daemon.daemon import DaemonIterator, IntervalDaemon

CURSOR_KEY = "ASSET_DAEMON_CURSOR"
ASSET_DAEMON_PAUSED_KEY = "ASSET_DAEMON_PAUSED"

EVALUATIONS_TTL_DAYS = 7


def get_auto_materialize_paused(instance: DagsterInstance) -> bool:
    return (
        instance.daemon_cursor_storage.get_cursor_values({ASSET_DAEMON_PAUSED_KEY}).get(
            ASSET_DAEMON_PAUSED_KEY
        )
        != "false"
    )


def set_auto_materialize_paused(instance: DagsterInstance, paused: bool):
    instance.daemon_cursor_storage.set_cursor_values(
        {ASSET_DAEMON_PAUSED_KEY: "true" if paused else "false"}
    )


def _get_raw_cursor(instance: DagsterInstance) -> Optional[str]:
    return instance.daemon_cursor_storage.get_cursor_values({CURSOR_KEY}).get(CURSOR_KEY)


def get_current_evaluation_id(instance: DagsterInstance) -> Optional[int]:
    raw_cursor = _get_raw_cursor(instance)
    return AssetDaemonCursor.get_evaluation_id_from_serialized(raw_cursor) if raw_cursor else None


class AssetDaemon(IntervalDaemon):
    def __init__(self, interval_seconds: int):
        super().__init__(interval_seconds=interval_seconds)

    @classmethod
    def daemon_type(cls) -> str:
        return "ASSET"

    def run_iteration(
        self,
        workspace_process_context: IWorkspaceProcessContext,
    ) -> DaemonIterator:
        instance = workspace_process_context.instance

        if get_auto_materialize_paused(instance):
            yield
            return

        schedule_storage = check.not_none(
            instance.schedule_storage,
            "Auto materialization requires schedule storage to be configured",
        )

        if not schedule_storage.supports_auto_materialize_asset_evaluations:
            self._logger.warning(
                "Auto materialize evaluations are not getting logged. Run `dagster instance"
                " migrate` to enable."
            )

        workspace = workspace_process_context.create_request_context()
        asset_graph = ExternalAssetGraph.from_workspace(workspace)
        target_asset_keys = {
            target_key
            for target_key in asset_graph.materializable_asset_keys
            if asset_graph.get_auto_materialize_policy(target_key) is not None
        }

        has_auto_observe_assets = any(
            asset_graph.get_auto_observe_interval_minutes(key) is not None
            for key in asset_graph.source_asset_keys
        )

        if not target_asset_keys and not has_auto_observe_assets:
            yield
            return

        raw_cursor = _get_raw_cursor(instance)
        cursor = (
            AssetDaemonCursor.from_serialized(raw_cursor, asset_graph)
            if raw_cursor
            else AssetDaemonCursor.empty()
        )

        run_requests, new_cursor, evaluations = AssetDaemonContext(
            asset_graph=asset_graph,
            target_asset_keys=target_asset_keys,
            instance=instance,
            cursor=cursor,
            materialize_run_tags={
                AUTO_MATERIALIZE_TAG: "true",
                **instance.auto_materialize_run_tags,
            },
            observe_run_tags={AUTO_OBSERVE_TAG: "true"},
            auto_observe=True,
        ).evaluate()

        evaluations_by_asset_key = {evaluation.asset_key: evaluation for evaluation in evaluations}

        for run_request in run_requests:
            yield

            asset_keys = check.not_none(run_request.asset_selection)

            run = submit_asset_run(
                run_request._replace(
                    tags={
                        **run_request.tags,
                        ASSET_EVALUATION_ID_TAG: str(new_cursor.evaluation_id),
                    }
                ),
                instance,
                workspace,
                asset_graph,
            )

            # add run id to evaluations
            for asset_key in asset_keys:
                # asset keys for observation runs don't have evaluations
                if asset_key in evaluations_by_asset_key:
                    evaluation = evaluations_by_asset_key[asset_key]
                    evaluations_by_asset_key[asset_key] = evaluation._replace(
                        run_ids=evaluation.run_ids | {run.run_id}
                    )

        instance.daemon_cursor_storage.set_cursor_values({CURSOR_KEY: new_cursor.serialize()})

        # We enforce uniqueness per (asset key, evaluation id). Store the evaluations after the cursor,
        # so that if the daemon crashes and doesn't update the cursor we don't try to write duplicates.
        if schedule_storage.supports_auto_materialize_asset_evaluations:
            schedule_storage.add_auto_materialize_asset_evaluations(
                new_cursor.evaluation_id, list(evaluations_by_asset_key.values())
            )
            schedule_storage.purge_asset_evaluations(
                before=pendulum.now("UTC").subtract(days=EVALUATIONS_TTL_DAYS).timestamp(),
            )


def submit_asset_run(
    run_request: RunRequest,
    instance: DagsterInstance,
    workspace: IWorkspace,
    asset_graph: ExternalAssetGraph,
) -> DagsterRun:
    asset_keys = check.not_none(run_request.asset_selection)
    check.invariant(len(asset_keys) > 0)

    repo_handle = asset_graph.get_repository_handle(asset_keys[0])

    # Check that all asset keys are from the same repo
    for key in asset_keys[1:]:
        check.invariant(repo_handle == asset_graph.get_repository_handle(key))

    location_name = repo_handle.code_location_origin.location_name
    repository_name = repo_handle.repository_name
    job_name = check.not_none(asset_graph.get_implicit_job_name_for_assets(asset_keys))

    code_location = workspace.get_code_location(location_name)
    external_job = code_location.get_external_job(
        JobSubsetSelector(
            location_name=location_name,
            repository_name=repository_name,
            job_name=job_name,
            op_selection=None,
            asset_selection=asset_keys,
        )
    )

    external_execution_plan = code_location.get_external_execution_plan(
        external_job,
        run_request.run_config,
        step_keys_to_execute=None,
        known_state=None,
        instance=instance,
    )
    execution_plan_snapshot = external_execution_plan.execution_plan_snapshot

    run = instance.create_run(
        job_name=external_job.name,
        run_id=None,
        run_config=None,
        resolved_op_selection=None,
        step_keys_to_execute=None,
        status=DagsterRunStatus.NOT_STARTED,
        op_selection=None,
        root_run_id=None,
        parent_run_id=None,
        tags=run_request.tags,
        job_snapshot=external_job.job_snapshot,
        execution_plan_snapshot=execution_plan_snapshot,
        parent_job_snapshot=external_job.parent_job_snapshot,
        external_job_origin=external_job.get_external_origin(),
        job_code_origin=external_job.get_python_origin(),
        asset_selection=frozenset(asset_keys),
    )
    instance.submit_run(run.run_id, workspace)
    return run
