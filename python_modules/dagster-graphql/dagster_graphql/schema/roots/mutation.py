import graphene

import dagster._check as check
from dagster.core.definitions.events import AssetKey
from dagster.core.workspace.permissions import Permissions

from ...implementation.execution import (
    cancel_partition_backfill,
    create_and_launch_partition_backfill,
    delete_pipeline_run,
    launch_pipeline_execution,
    launch_pipeline_reexecution,
    launch_reexecution_from_parent_run,
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
from ..inputs import (
    GrapheneAssetKeyInput,
    GrapheneExecutionParams,
    GrapheneLaunchBackfillParams,
    GrapheneReexecutionParams,
)
from ..pipelines.pipeline import GrapheneRun
from ..runs import (
    GrapheneLaunchRunReexecutionResult,
    GrapheneLaunchRunResult,
    parse_run_config_input,
)
from ..schedules import GrapheneStartScheduleMutation, GrapheneStopRunningScheduleMutation
from ..sensors import (
    GrapheneSetSensorCursorMutation,
    GrapheneStartSensorMutation,
    GrapheneStopSensorMutation,
)
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
        run_config=parse_run_config_input(graphql_execution_params.get("runConfigData") or {}),
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
    """Output indicating that a run was deleted."""

    runId = graphene.NonNull(graphene.String)

    class Meta:
        name = "DeletePipelineRunSuccess"


class GrapheneDeletePipelineRunResult(graphene.Union):
    """The output from deleting a run."""

    class Meta:
        types = (
            GrapheneDeletePipelineRunSuccess,
            GrapheneUnauthorizedError,
            GraphenePythonError,
            GrapheneRunNotFoundError,
        )
        name = "DeletePipelineRunResult"


class GrapheneDeleteRunMutation(graphene.Mutation):
    """Deletes a run from storage."""

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
    """Interface indicating that a run was terminated."""

    run = graphene.Field(graphene.NonNull(GrapheneRun))

    class Meta:
        name = "TerminatePipelineExecutionSuccess"


class GrapheneTerminateRunSuccess(graphene.ObjectType):
    """Output indicating that a run was terminated."""

    run = graphene.Field(graphene.NonNull(GrapheneRun))

    class Meta:
        interfaces = (GrapheneTerminatePipelineExecutionSuccess,)
        name = "TerminateRunSuccess"


class GrapheneTerminatePipelineExecutionFailure(graphene.Interface):
    """Interface indicating that a run failed to terminate."""

    run = graphene.NonNull(GrapheneRun)
    message = graphene.NonNull(graphene.String)

    class Meta:
        name = "TerminatePipelineExecutionFailure"


class GrapheneTerminateRunFailure(graphene.ObjectType):
    """Output indicating that a run failed to terminate."""

    run = graphene.NonNull(GrapheneRun)
    message = graphene.NonNull(graphene.String)

    class Meta:
        interfaces = (GrapheneTerminatePipelineExecutionFailure,)
        name = "TerminateRunFailure"


class GrapheneTerminateRunResult(graphene.Union):
    """The output from a run termination."""

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
    """Launches a job run."""

    Output = graphene.NonNull(GrapheneLaunchRunResult)

    class Arguments:
        executionParams = graphene.NonNull(GrapheneExecutionParams)

    class Meta:
        name = "LaunchRunMutation"

    @capture_error
    @check_permission(Permissions.LAUNCH_PIPELINE_EXECUTION)
    def mutate(self, graphene_info, **kwargs):
        return create_execution_params_and_launch_pipeline_exec(
            graphene_info, kwargs["executionParams"]
        )


class GrapheneLaunchBackfillMutation(graphene.Mutation):
    """Launches a set of partition backfill runs."""

    Output = graphene.NonNull(GrapheneLaunchBackfillResult)

    class Arguments:
        backfillParams = graphene.NonNull(GrapheneLaunchBackfillParams)

    class Meta:
        name = "LaunchBackfillMutation"

    @capture_error
    @check_permission(Permissions.LAUNCH_PARTITION_BACKFILL)
    def mutate(self, graphene_info, **kwargs):
        return create_and_launch_partition_backfill(graphene_info, kwargs["backfillParams"])


class GrapheneCancelBackfillMutation(graphene.Mutation):
    """Cancels a set of partition backfill runs."""

    Output = graphene.NonNull(GrapheneCancelBackfillResult)

    class Arguments:
        backfillId = graphene.NonNull(graphene.String)

    class Meta:
        name = "CancelBackfillMutation"

    @capture_error
    @check_permission(Permissions.CANCEL_PARTITION_BACKFILL)
    def mutate(self, graphene_info, **kwargs):
        return cancel_partition_backfill(graphene_info, kwargs["backfillId"])


class GrapheneResumeBackfillMutation(graphene.Mutation):
    """Retries a set of partition backfill runs."""

    Output = graphene.NonNull(GrapheneResumeBackfillResult)

    class Arguments:
        backfillId = graphene.NonNull(graphene.String)

    class Meta:
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
    """Re-executes a job run."""

    Output = graphene.NonNull(GrapheneLaunchRunReexecutionResult)

    class Arguments:
        executionParams = graphene.Argument(GrapheneExecutionParams)
        reexecutionParams = graphene.Argument(GrapheneReexecutionParams)

    class Meta:
        name = "LaunchRunReexecutionMutation"

    @capture_error
    @check_permission(Permissions.LAUNCH_PIPELINE_REEXECUTION)
    def mutate(self, graphene_info, **kwargs):
        execution_params = kwargs.get("executionParams")
        reexecution_params = kwargs.get("reexecutionParams")
        check.invariant(
            bool(execution_params) != bool(reexecution_params),
            "Must only provide one of either executionParams or reexecutionParams",
        )

        if execution_params:
            return create_execution_params_and_launch_pipeline_reexec(
                graphene_info,
                execution_params_dict=kwargs["executionParams"],
            )
        else:
            return launch_reexecution_from_parent_run(
                graphene_info,
                reexecution_params["parentRunId"],
                reexecution_params["strategy"],
            )


class GrapheneTerminateRunPolicy(graphene.Enum):
    """The type of termination policy to use for a run."""

    # Default behavior: Only mark as canceled if the termination is successful, and after all
    # resources performing the execution have been shut down.
    SAFE_TERMINATE = "SAFE_TERMINATE"

    # Immediately mark the run as canceled, whether or not the termination was successful.
    # No guarantee that the execution has actually stopped.
    MARK_AS_CANCELED_IMMEDIATELY = "MARK_AS_CANCELED_IMMEDIATELY"

    class Meta:
        name = "TerminateRunPolicy"


class GrapheneTerminateRunMutation(graphene.Mutation):
    """Terminates a run."""

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
            graphene_info.context.instance,
            kwargs["runId"],
            kwargs.get("terminatePolicy", GrapheneTerminateRunPolicy.SAFE_TERMINATE),
        )


class GrapheneReloadRepositoryLocationMutationResult(graphene.Union):
    """The output from reloading a code location server."""

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
    """Output indicating that a code location server was shut down."""

    repositoryLocationName = graphene.NonNull(graphene.String)

    class Meta:
        name = "ShutdownRepositoryLocationSuccess"


class GrapheneShutdownRepositoryLocationMutationResult(graphene.Union):
    """The output from shutting down a code location server."""

    class Meta:
        types = (
            GrapheneShutdownRepositoryLocationSuccess,
            GrapheneRepositoryLocationNotFound,
            GrapheneUnauthorizedError,
            GraphenePythonError,
        )
        name = "ShutdownRepositoryLocationMutationResult"


class GrapheneReloadRepositoryLocationMutation(graphene.Mutation):
    """Reloads a code location server."""

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
    """Shuts down a code location server."""

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
    """The output from reloading the workspace."""

    class Meta:
        types = (
            GrapheneWorkspace,
            GrapheneUnauthorizedError,
            GraphenePythonError,
        )
        name = "ReloadWorkspaceMutationResult"


class GrapheneReloadWorkspaceMutation(graphene.Mutation):
    """Reloads the workspace and its code location servers."""

    Output = graphene.NonNull(GrapheneReloadWorkspaceMutationResult)

    class Meta:
        name = "ReloadWorkspaceMutation"

    @capture_error
    @check_permission(Permissions.RELOAD_WORKSPACE)
    def mutate(self, graphene_info, **_kwargs):
        new_context = graphene_info.context.reload_workspace()
        return fetch_workspace(new_context)


class GrapheneAssetWipeSuccess(graphene.ObjectType):
    """Output indicating that asset history was deleted."""

    assetKeys = non_null_list(GrapheneAssetKey)

    class Meta:
        name = "AssetWipeSuccess"


class GrapheneAssetWipeMutationResult(graphene.Union):
    """The output from deleting asset history."""

    class Meta:
        types = (
            GrapheneAssetNotFoundError,
            GrapheneUnauthorizedError,
            GraphenePythonError,
            GrapheneAssetWipeSuccess,
        )
        name = "AssetWipeMutationResult"


class GrapheneAssetWipeMutation(graphene.Mutation):
    """Deletes asset history from storage."""

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
    """Output indicating that telemetry was logged."""

    action = graphene.NonNull(graphene.String)

    class Meta:
        name = "LogTelemetrySuccess"


class GrapheneLogTelemetryMutationResult(graphene.Union):
    """The output from logging telemetry."""

    class Meta:
        types = (
            GrapheneLogTelemetrySuccess,
            GraphenePythonError,
        )
        name = "LogTelemetryMutationResult"


class GrapheneLogTelemetryMutation(graphene.Mutation):
    """Log telemetry about the Dagster instance."""

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
    """Mutations to programatically interact with your Dagster instance."""

    class Meta:
        name = "DagitMutation"

    launch_pipeline_execution = GrapheneLaunchRunMutation.Field()
    launch_run = GrapheneLaunchRunMutation.Field()
    launch_pipeline_reexecution = GrapheneLaunchRunReexecutionMutation.Field()
    launch_run_reexecution = GrapheneLaunchRunReexecutionMutation.Field()
    start_schedule = GrapheneStartScheduleMutation.Field()
    stop_running_schedule = GrapheneStopRunningScheduleMutation.Field()
    start_sensor = GrapheneStartSensorMutation.Field()
    set_sensor_cursor = GrapheneSetSensorCursorMutation.Field()
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
