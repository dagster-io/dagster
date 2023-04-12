import dagster._check as check
from dagster._core.definitions.asset_reconciliation_sensor import (
    AssetReconciliationCursor,
    reconcile,
)
from dagster._core.definitions.external_asset_graph import ExternalAssetGraph
from dagster._core.definitions.mode import DEFAULT_MODE_NAME
from dagster._core.definitions.selector import PipelineSelector
from dagster._core.storage.pipeline_run import DagsterRunStatus
from dagster._core.storage.tags import CREATED_BY_TAG
from dagster._core.workspace.context import IWorkspaceProcessContext
from dagster._daemon.daemon import DaemonIterator, IntervalDaemon

CURSOR_NAME = "ASSET_DAEMON_CURSOR"


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
        workspace = workspace_process_context.create_request_context()
        asset_graph = ExternalAssetGraph.from_workspace(workspace)

        target_asset_keys = {
            target_key
            for target_key in asset_graph.non_source_asset_keys
            if asset_graph.get_auto_materialize_policy(target_key) is not None
        }

        if not target_asset_keys:
            yield
            return

        raw_cursor = instance.run_storage.kvs_get({CURSOR_NAME}).get(CURSOR_NAME)
        cursor = (
            AssetReconciliationCursor.from_serialized(raw_cursor, asset_graph)
            if raw_cursor
            else AssetReconciliationCursor.empty()
        )

        run_requests, new_cursor = reconcile(
            asset_graph=asset_graph,
            target_asset_keys=target_asset_keys,
            instance=instance,
            cursor=cursor,
            run_tags=None,
        )

        for run_request in run_requests:
            yield

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
            external_pipeline = code_location.get_external_pipeline(
                PipelineSelector(
                    location_name=location_name,
                    repository_name=repository_name,
                    pipeline_name=job_name,
                    solid_selection=None,
                    asset_selection=asset_keys,
                )
            )

            tags = {
                **run_request.tags,
                CREATED_BY_TAG: "auto_materialize",
            }

            external_execution_plan = code_location.get_external_execution_plan(
                external_pipeline,
                run_request.run_config,
                DEFAULT_MODE_NAME,
                step_keys_to_execute=None,
                known_state=None,
                instance=instance,
            )
            execution_plan_snapshot = external_execution_plan.execution_plan_snapshot

            run = instance.create_run(
                pipeline_name=external_pipeline.name,
                run_id=None,
                run_config=None,
                mode=DEFAULT_MODE_NAME,
                solids_to_execute=None,
                step_keys_to_execute=None,
                status=DagsterRunStatus.NOT_STARTED,
                solid_selection=None,
                root_run_id=None,
                parent_run_id=None,
                tags=tags,
                pipeline_snapshot=external_pipeline.pipeline_snapshot,
                execution_plan_snapshot=execution_plan_snapshot,
                parent_pipeline_snapshot=external_pipeline.parent_pipeline_snapshot,
                external_pipeline_origin=external_pipeline.get_external_origin(),
                pipeline_code_origin=external_pipeline.get_python_origin(),
                asset_selection=frozenset(asset_keys),
            )
            instance.submit_run(run.run_id, workspace)

        instance.run_storage.kvs_set({CURSOR_NAME: new_cursor.serialize()})
