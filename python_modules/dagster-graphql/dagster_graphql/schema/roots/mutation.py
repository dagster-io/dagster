import graphene
from dagster.core.definitions.events import AssetKey
from dagster.core.workspace.permissions import Permissions

from ...implementation.execution import (
    cancel_partition_backfill,
    create_and_launch_partition_backfill,
    delete_pipeline_run,
    launch_pipeline_execution,
    launch_pipeline_reexecution,
    resume_partition_backfill,
    terminate_pipeline_execution,
    wipe_assets,
)
from ...implementation.external import fetch_workspace, get_full_external_pipeline_or_raise
from ...implementation.telemetry import log_dagit_telemetry_event
from ...implementation.utils import (
    ExecutionMetadata,
    ExecutionParams,
    UserFacingGraphQLError,
    capture_error,
    check_permission,
    pipeline_selector_from_graphql,
)
from ..asset_key import GrapheneAssetKey
from ..backfill import (
    GrapheneCancelBackfillResult,
    GrapheneLaunchBackfillResult,
    GrapheneResumeBackfillResult,
)
from ..errors import (
    GrapheneAssetNotFoundError,
    GrapheneConflictingExecutionParamsError,
    GraphenePresetNotFoundError,
    GraphenePythonError,
    GrapheneReloadNotSupported,
    GrapheneRepositoryLocationNotFound,
    GrapheneRunNotFoundError,
    GrapheneUnauthorizedError,
)
from ..external import GrapheneWorkspace, GrapheneWorkspaceLocationEntry
from ..inputs import GrapheneAssetKeyInput, GrapheneExecutionParams, GrapheneLaunchBackfillParams
from ..pipelines.pipeline import GrapheneRun
from ..runs import GrapheneLaunchRunReexecutionResult, GrapheneLaunchRunResult
from ..schedules import GrapheneStartScheduleMutation, GrapheneStopRunningScheduleMutation
from ..sensors import GrapheneStartSensorMutation, GrapheneStopSensorMutation
from ..util import non_null_list


def create_execution_params(graphene_info, graphql_execution_params):
    preset_name = graphql_execution_params.get("preset")
    selector = pipeline_selector_from_graphql(graphql_execution_params["selector"])
    if preset_name:
        if graphql_execution_params.get("runConfigData"):
            raise UserFacingGraphQLError(
                GrapheneConflictingExecutionParamsError(conflicting_param="runConfigData")
            )

        if graphql_execution_params.get("mode"):
            raise UserFacingGraphQLError(
                GrapheneConflictingExecutionParamsError(conflicting_param="mode")
            )

        if selector.solid_selection:
            raise UserFacingGraphQLError(
                GrapheneConflictingExecutionParamsError(
                    conflicting_param="selector.solid_selection"
                )
            )

        external_pipeline = get_full_external_pipeline_or_raise(graphene_info, selector)

        if not external_pipeline.has_preset(preset_name):
            raise UserFacingGraphQLError(
                GraphenePresetNotFoundError(preset=preset_name, selector=selector)
            )

        preset = external_pipeline.get_preset(preset_name)

        return ExecutionParams(
            selector=selector.with_solid_selection(preset.solid_selection),
            run_config=preset.run_config,
            mode=preset.mode,
            execution_metadata=create_execution_metadata(
                graphql_execution_params.get("executionMetadata")
            ),
            step_keys=graphql_execution_params.get("stepKeys"),
        )

    return execution_params_from_graphql(graphql_execution_params)


def execution_params_from_graphql(graphql_execution_params):
    return ExecutionParams(
        selector=pipeline_selector_from_graphql(graphql_execution_params.get("selector")),
        run_config=graphql_execution_params.get("runConfigData") or {},
        mode=graphql_execution_params.get("mode"),
        execution_metadata=create_execution_metadata(
            graphql_execution_params.get("executionMetadata")
        ),
        step_keys=graphql_execution_params.get("stepKeys"),
    )


def create_execution_metadata(graphql_execution_metadata):
    return (
        ExecutionMetadata(
            run_id=graphql_execution_metadata.get("runId"),
            tags={t["key"]: t["value"] for t in graphql_execution_metadata.get("tags", [])},
            root_run_id=graphql_execution_metadata.get("rootRunId"),
            parent_run_id=graphql_execution_metadata.get("parentRunId"),
        )
        if graphql_execution_metadata
        else ExecutionMetadata(run_id=None, tags={})
    )


class GrapheneDeletePipelineRunSuccess(graphene.ObjectType):
    runId = graphene.NonNull(graphene.String)

    class Meta:
        name = "DeletePipelineRunSuccess"


class GrapheneDeletePipelineRunResult(graphene.Union):
    class Meta:
        types = (
            GrapheneDeletePipelineRunSuccess,
            GrapheneUnauthorizedError,
            GraphenePythonError,
            GrapheneRunNotFoundError,
        )
        name = "DeletePipelineRunResult"


class GrapheneDeleteRunMutation(graphene.Mutation):
    Output = graphene.NonNull(GrapheneDeletePipelineRunResult)

    class Arguments:
        runId = graphene.NonNull(graphene.String)

    class Meta:
        name = "DeleteRunMutation"

    @capture_error
    @check_permission(Permissions.DELETE_PIPELINE_RUN)
    def mutate(self, graphene_info, **kwargs):
        run_id = kwargs["runId"]
        return delete_pipeline_run(graphene_info, run_id)


class GrapheneTerminatePipelineExecutionSuccess(graphene.Interface):
    run = graphene.Field(graphene.NonNull(GrapheneRun))

    class Meta:
        name = "TerminatePipelineExecutionSuccess"


class GrapheneTerminateRunSuccess(graphene.ObjectType):
    run = graphene.Field(graphene.NonNull(GrapheneRun))

    class Meta:
        interfaces = (GrapheneTerminatePipelineExecutionSuccess,)
        name = "TerminateRunSuccess"


class GrapheneTerminatePipelineExecutionFailure(graphene.Interface):
    run = graphene.NonNull(GrapheneRun)
    message = graphene.NonNull(graphene.String)

    class Meta:
        name = "TerminatePipelineExecutionFailure"


class GrapheneTerminateRunFailure(graphene.ObjectType):
    run = graphene.NonNull(GrapheneRun)
    message = graphene.NonNull(graphene.String)

    class Meta:
        interfaces = (GrapheneTerminatePipelineExecutionFailure,)
        name = "TerminateRunFailure"


class GrapheneTerminateRunResult(graphene.Union):
    class Meta:
        types = (
            GrapheneTerminateRunSuccess,
            GrapheneTerminateRunFailure,
            GrapheneRunNotFoundError,
            GrapheneUnauthorizedError,
            GraphenePythonError,
        )
        name = "TerminateRunResult"


@capture_error
def create_execution_params_and_launch_pipeline_exec(graphene_info, execution_params_dict):
    # refactored into a helper function here in order to wrap with @capture_error,
    # because create_execution_params may raise
    return launch_pipeline_execution(
        graphene_info,
        execution_params=create_execution_params(graphene_info, execution_params_dict),
    )


class GrapheneLaunchRunMutation(graphene.Mutation):

    Output = graphene.NonNull(GrapheneLaunchRunResult)

    class Arguments:
        executionParams = graphene.NonNull(GrapheneExecutionParams)

    class Meta:
        description = "Launch a run via the run launcher configured on the instance."
        name = "LaunchRunMutation"

    @capture_error
    @check_permission(Permissions.LAUNCH_PIPELINE_EXECUTION)
    def mutate(self, graphene_info, **kwargs):
        return create_execution_params_and_launch_pipeline_exec(
            graphene_info, kwargs["executionParams"]
        )


class GrapheneLaunchBackfillMutation(graphene.Mutation):
    Output = graphene.NonNull(GrapheneLaunchBackfillResult)

    class Arguments:
        backfillParams = graphene.NonNull(GrapheneLaunchBackfillParams)

    class Meta:
        description = "Launches a set of partition backfill runs via the run launcher configured on the instance."
        name = "LaunchBackfillMutation"

    @capture_error
    @check_permission(Permissions.LAUNCH_PARTITION_BACKFILL)
    def mutate(self, graphene_info, **kwargs):
        return create_and_launch_partition_backfill(graphene_info, kwargs["backfillParams"])


class GrapheneCancelBackfillMutation(graphene.Mutation):
    Output = graphene.NonNull(GrapheneCancelBackfillResult)

    class Arguments:
        backfillId = graphene.NonNull(graphene.String)

    class Meta:
        description = "Marks a partition backfill as canceled."
        name = "CancelBackfillMutation"

    @capture_error
    @check_permission(Permissions.CANCEL_PARTITION_BACKFILL)
    def mutate(self, graphene_info, **kwargs):
        return cancel_partition_backfill(graphene_info, kwargs["backfillId"])


class GrapheneResumeBackfillMutation(graphene.Mutation):
    Output = graphene.NonNull(GrapheneResumeBackfillResult)

    class Arguments:
        backfillId = graphene.NonNull(graphene.String)

    class Meta:
        description = "Retries a set of partition backfill runs via the run launcher configured on the instance."
        name = "ResumeBackfillMutation"

    @capture_error
    @check_permission(Permissions.LAUNCH_PARTITION_BACKFILL)
    def mutate(self, graphene_info, **kwargs):
        return resume_partition_backfill(graphene_info, kwargs["backfillId"])


@capture_error
def create_execution_params_and_launch_pipeline_reexec(graphene_info, execution_params_dict):
    # refactored into a helper function here in order to wrap with @capture_error,
    # because create_execution_params may raise
    return launch_pipeline_reexecution(
        graphene_info,
        execution_params=create_execution_params(graphene_info, execution_params_dict),
    )


class GrapheneLaunchRunReexecutionMutation(graphene.Mutation):
    Output = graphene.NonNull(GrapheneLaunchRunReexecutionResult)

    class Arguments:
        executionParams = graphene.NonNull(GrapheneExecutionParams)

    class Meta:
        description = "Re-launch a run via the run launcher configured on the instance"
        name = "LaunchRunReexecutionMutation"

    @capture_error
    @check_permission(Permissions.LAUNCH_PIPELINE_REEXECUTION)
    def mutate(self, graphene_info, **kwargs):
        return create_execution_params_and_launch_pipeline_reexec(
            graphene_info,
            execution_params_dict=kwargs["executionParams"],
        )


class GrapheneTerminateRunPolicy(graphene.Enum):
    # Default behavior: Only mark as canceled if the termination is successful, and after all
    # resources peforming the execution have been shut down.
    SAFE_TERMINATE = "SAFE_TERMINATE"

    # Immediately mark the pipelie as canceled, whether or not the termination was successful.
    # No guarantee that the execution has actually stopped.
    MARK_AS_CANCELED_IMMEDIATELY = "MARK_AS_CANCELED_IMMEDIATELY"

    class Meta:
        name = "TerminateRunPolicy"


class GrapheneTerminateRunMutation(graphene.Mutation):
    Output = graphene.NonNull(GrapheneTerminateRunResult)

    class Arguments:
        runId = graphene.NonNull(graphene.String)
        terminatePolicy = graphene.Argument(GrapheneTerminateRunPolicy)

    class Meta:
        name = "TerminateRunMutation"

    @capture_error
    @check_permission(Permissions.TERMINATE_PIPELINE_EXECUTION)
    def mutate(self, graphene_info, **kwargs):
        return terminate_pipeline_execution(
            graphene_info,
            kwargs["runId"],
            kwargs.get("terminatePolicy", GrapheneTerminateRunPolicy.SAFE_TERMINATE),
        )


class GrapheneReloadRepositoryLocationMutationResult(graphene.Union):
    class Meta:
        types = (
            GrapheneWorkspaceLocationEntry,
            GrapheneReloadNotSupported,
            GrapheneRepositoryLocationNotFound,
            GrapheneUnauthorizedError,
            GraphenePythonError,
        )
        name = "ReloadRepositoryLocationMutationResult"


class GrapheneShutdownRepositoryLocationSuccess(graphene.ObjectType):
    repositoryLocationName = graphene.NonNull(graphene.String)

    class Meta:
        name = "ShutdownRepositoryLocationSuccess"


class GrapheneShutdownRepositoryLocationMutationResult(graphene.Union):
    class Meta:
        types = (
            GrapheneShutdownRepositoryLocationSuccess,
            GrapheneRepositoryLocationNotFound,
            GrapheneUnauthorizedError,
            GraphenePythonError,
        )
        name = "ShutdownRepositoryLocationMutationResult"


class GrapheneReloadRepositoryLocationMutation(graphene.Mutation):
    Output = graphene.NonNull(GrapheneReloadRepositoryLocationMutationResult)

    class Arguments:
        repositoryLocationName = graphene.NonNull(graphene.String)

    class Meta:
        name = "ReloadRepositoryLocationMutation"

    @capture_error
    @check_permission(Permissions.RELOAD_REPOSITORY_LOCATION)
    def mutate(self, graphene_info, **kwargs):
        location_name = kwargs["repositoryLocationName"]

        if not graphene_info.context.has_repository_location_name(location_name):
            return GrapheneRepositoryLocationNotFound(location_name)

        if not graphene_info.context.is_reload_supported(location_name):
            return GrapheneReloadNotSupported(location_name)

        # The current workspace context is a WorkspaceRequestContext, which contains a reference to the
        # repository locations that were present in the root IWorkspaceProcessContext the start of the
        # request. Reloading a repository location modifies the IWorkspaceProcessContext, rendeirng
        # our current WorkspaceRequestContext outdated. Therefore, `reload_repository_location` returns
        # an updated WorkspaceRequestContext for us to use.
        new_context = graphene_info.context.reload_repository_location(location_name)
        return GrapheneWorkspaceLocationEntry(new_context.get_location_entry(location_name))


class GrapheneShutdownRepositoryLocationMutation(graphene.Mutation):
    Output = graphene.NonNull(GrapheneShutdownRepositoryLocationMutationResult)

    class Arguments:
        repositoryLocationName = graphene.NonNull(graphene.String)

    class Meta:
        name = "ShutdownRepositoryLocationMutation"

    @capture_error
    @check_permission(Permissions.RELOAD_REPOSITORY_LOCATION)
    def mutate(self, graphene_info, **kwargs):
        location_name = kwargs["repositoryLocationName"]

        if not graphene_info.context.has_repository_location_name(location_name):
            return GrapheneRepositoryLocationNotFound(location_name)

        if not graphene_info.context.is_shutdown_supported(location_name):
            raise Exception(f"Location {location_name} does not support shutting down via GraphQL")

        graphene_info.context.shutdown_repository_location(location_name)
        return GrapheneShutdownRepositoryLocationSuccess(repositoryLocationName=location_name)


class GrapheneReloadWorkspaceMutationResult(graphene.Union):
    class Meta:
        types = (
            GrapheneWorkspace,
            GrapheneUnauthorizedError,
            GraphenePythonError,
        )
        name = "ReloadWorkspaceMutationResult"


class GrapheneReloadWorkspaceMutation(graphene.Mutation):
    Output = graphene.NonNull(GrapheneReloadWorkspaceMutationResult)

    class Meta:
        name = "ReloadWorkspaceMutation"

    @capture_error
    @check_permission(Permissions.RELOAD_WORKSPACE)
    def mutate(self, graphene_info, **_kwargs):
        new_context = graphene_info.context.reload_workspace()
        return fetch_workspace(new_context)


class GrapheneAssetWipeSuccess(graphene.ObjectType):
    assetKeys = non_null_list(GrapheneAssetKey)

    class Meta:
        name = "AssetWipeSuccess"


class GrapheneAssetWipeMutationResult(graphene.Union):
    class Meta:
        types = (
            GrapheneAssetNotFoundError,
            GrapheneUnauthorizedError,
            GraphenePythonError,
            GrapheneAssetWipeSuccess,
        )
        name = "AssetWipeMutationResult"


class GrapheneAssetWipeMutation(graphene.Mutation):
    Output = graphene.NonNull(GrapheneAssetWipeMutationResult)

    class Arguments:
        assetKeys = graphene.Argument(non_null_list(GrapheneAssetKeyInput))

    class Meta:
        name = "AssetWipeMutation"

    @capture_error
    @check_permission(Permissions.WIPE_ASSETS)
    def mutate(self, graphene_info, **kwargs):
        return wipe_assets(
            graphene_info,
            [AssetKey.from_graphql_input(asset_key) for asset_key in kwargs["assetKeys"]],
        )


class GrapheneLogTelemetrySuccess(graphene.ObjectType):
    action = graphene.NonNull(graphene.String)

    class Meta:
        name = "LogTelemetrySuccess"


class GrapheneLogTelemetryMutationResult(graphene.Union):
    class Meta:
        types = (
            GrapheneLogTelemetrySuccess,
            GraphenePythonError,
        )
        name = "LogTelemetryMutationResult"


class GrapheneLogTelemetryMutation(graphene.Mutation):
    Output = graphene.NonNull(GrapheneLogTelemetryMutationResult)

    class Arguments:
        action = graphene.Argument(graphene.NonNull(graphene.String))
        clientTime = graphene.Argument(graphene.NonNull(graphene.String))
        metadata = graphene.Argument(graphene.NonNull(graphene.String))

    class Meta:
        name = "LogTelemetryMutation"

    @capture_error
    def mutate(self, graphene_info, **kwargs):
        action = log_dagit_telemetry_event(
            graphene_info,
            action=kwargs["action"],
            client_time=kwargs["clientTime"],
            metadata=kwargs["metadata"],
        )
        return action


class GrapheneDagitMutation(graphene.ObjectType):
    class Meta:
        name = "DagitMutation"

    launch_pipeline_execution = GrapheneLaunchRunMutation.Field()
    launch_run = GrapheneLaunchRunMutation.Field()
    launch_pipeline_reexecution = GrapheneLaunchRunReexecutionMutation.Field()
    launch_run_reexecution = GrapheneLaunchRunReexecutionMutation.Field()
    start_schedule = GrapheneStartScheduleMutation.Field()
    stop_running_schedule = GrapheneStopRunningScheduleMutation.Field()
    start_sensor = GrapheneStartSensorMutation.Field()
    stop_sensor = GrapheneStopSensorMutation.Field()
    terminate_pipeline_execution = GrapheneTerminateRunMutation.Field()
    terminate_run = GrapheneTerminateRunMutation.Field()
    delete_pipeline_run = GrapheneDeleteRunMutation.Field()
    delete_run = GrapheneDeleteRunMutation.Field()
    reload_repository_location = GrapheneReloadRepositoryLocationMutation.Field()
    reload_workspace = GrapheneReloadWorkspaceMutation.Field()
    shutdown_repository_location = GrapheneShutdownRepositoryLocationMutation.Field()
    wipe_assets = GrapheneAssetWipeMutation.Field()
    launch_partition_backfill = GrapheneLaunchBackfillMutation.Field()
    resume_partition_backfill = GrapheneResumeBackfillMutation.Field()
    cancel_partition_backfill = GrapheneCancelBackfillMutation.Field()
    log_telemetry = GrapheneLogTelemetryMutation.Field()
