from collections.abc import Sequence
from typing import Optional, Union

import dagster._check as check
import graphene
from dagster._core.definitions.events import AssetKey, AssetPartitionWipeRange
from dagster._core.definitions.partition_key_range import PartitionKeyRange
from dagster._core.errors import DagsterInvariantViolationError
from dagster._core.nux import get_has_seen_nux, set_nux_seen
from dagster._core.workspace.permissions import Permissions
from dagster._daemon.asset_daemon import set_auto_materialize_paused

from dagster_graphql.implementation.execution import (
    delete_pipeline_run,
    report_runless_asset_events,
    terminate_pipeline_execution,
    terminate_pipeline_execution_for_runs,
    wipe_assets,
)
from dagster_graphql.implementation.execution.backfill import (
    cancel_partition_backfill,
    create_and_launch_partition_backfill,
    resume_partition_backfill,
    retry_partition_backfill,
)
from dagster_graphql.implementation.execution.dynamic_partitions import (
    add_dynamic_partition,
    delete_dynamic_partitions,
)
from dagster_graphql.implementation.execution.launch_execution import (
    launch_pipeline_execution,
    launch_pipeline_reexecution,
    launch_reexecution_from_parent_run,
)
from dagster_graphql.implementation.external import fetch_workspace, get_full_remote_job_or_raise
from dagster_graphql.implementation.telemetry import log_ui_telemetry_event
from dagster_graphql.implementation.utils import (
    ExecutionMetadata,
    ExecutionParams,
    UserFacingGraphQLError,
    assert_permission_for_asset_graph,
    assert_permission_for_location,
    capture_error,
    check_permission,
    pipeline_selector_from_graphql,
    require_permission_check,
)
from dagster_graphql.schema.backfill import (
    GrapheneAssetPartitionRange,
    GrapheneCancelBackfillResult,
    GrapheneLaunchBackfillResult,
    GrapheneResumeBackfillResult,
)
from dagster_graphql.schema.entity_key import GrapheneAssetKey
from dagster_graphql.schema.errors import (
    GrapheneAssetNotFoundError,
    GrapheneConflictingExecutionParamsError,
    GrapheneError,
    GraphenePresetNotFoundError,
    GraphenePythonError,
    GrapheneReloadNotSupported,
    GrapheneRepositoryLocationNotFound,
    GrapheneRunNotFoundError,
    GrapheneUnauthorizedError,
    GrapheneUnsupportedOperationError,
)
from dagster_graphql.schema.external import GrapheneWorkspace, GrapheneWorkspaceLocationEntry
from dagster_graphql.schema.inputs import (
    GrapheneExecutionParams,
    GrapheneLaunchBackfillParams,
    GraphenePartitionsByAssetSelector,
    GrapheneReexecutionParams,
    GrapheneReportRunlessAssetEventsParams,
    GrapheneRepositorySelector,
)
from dagster_graphql.schema.partition_sets import (
    GrapheneAddDynamicPartitionResult,
    GrapheneDeleteDynamicPartitionsResult,
)
from dagster_graphql.schema.pipelines.pipeline import GrapheneRun
from dagster_graphql.schema.runs import (
    GrapheneLaunchMultipleRunsResult,
    GrapheneLaunchMultipleRunsResultOrError,
    GrapheneLaunchRunReexecutionResult,
    GrapheneLaunchRunResult,
    GrapheneLaunchRunSuccess,
    parse_run_config_input,
)
from dagster_graphql.schema.schedule_dry_run import GrapheneScheduleDryRunMutation
from dagster_graphql.schema.schedules import (
    GrapheneResetScheduleMutation,
    GrapheneStartScheduleMutation,
    GrapheneStopRunningScheduleMutation,
)
from dagster_graphql.schema.sensor_dry_run import GrapheneSensorDryRunMutation
from dagster_graphql.schema.sensors import (
    GrapheneResetSensorMutation,
    GrapheneSetSensorCursorMutation,
    GrapheneStartSensorMutation,
    GrapheneStopSensorMutation,
)
from dagster_graphql.schema.util import ResolveInfo, non_null_list


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

        if selector.op_selection:
            raise UserFacingGraphQLError(
                GrapheneConflictingExecutionParamsError(
                    conflicting_param="selector.solid_selection"
                )
            )

        external_pipeline = get_full_remote_job_or_raise(
            graphene_info,
            selector,
        )

        if not external_pipeline.has_preset(preset_name):
            raise UserFacingGraphQLError(
                GraphenePresetNotFoundError(preset=preset_name, selector=selector)
            )

        preset = external_pipeline.get_preset(preset_name)

        return ExecutionParams(
            selector=selector.with_op_selection(preset.op_selection),
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
        run_config=parse_run_config_input(  # pyright: ignore[reportArgumentType]
            graphql_execution_params.get("runConfigData") or {},
            raise_on_error=True,
        ),
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
    @require_permission_check(Permissions.DELETE_PIPELINE_RUN)
    def mutate(
        self, graphene_info: ResolveInfo, runId: str
    ) -> Union[GrapheneRunNotFoundError, GrapheneDeletePipelineRunSuccess]:
        return delete_pipeline_run(graphene_info, runId)


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


class GrapheneTerminateRunsResult(graphene.ObjectType):
    """Indicates the runs that successfully terminated and those that failed to terminate."""

    terminateRunResults = non_null_list(GrapheneTerminateRunResult)

    class Meta:
        name = "TerminateRunsResult"


class GrapheneTerminateRunsResultOrError(graphene.Union):
    """The output from runs termination."""

    class Meta:
        types = (GrapheneTerminateRunsResult, GraphenePythonError)
        name = "TerminateRunsResultOrError"


def create_execution_params_and_launch_pipeline_exec(graphene_info, execution_params_dict):
    execution_params = create_execution_params(graphene_info, execution_params_dict)
    assert_permission_for_location(
        graphene_info,
        Permissions.LAUNCH_PIPELINE_EXECUTION,
        execution_params.selector.location_name,
    )
    return launch_pipeline_execution(
        graphene_info,
        execution_params,
    )


class GrapheneLaunchRunMutation(graphene.Mutation):
    """Launches a job run."""

    Output = graphene.NonNull(GrapheneLaunchRunResult)

    class Arguments:
        executionParams = graphene.NonNull(GrapheneExecutionParams)

    class Meta:
        name = "LaunchRunMutation"

    @capture_error
    @require_permission_check(Permissions.LAUNCH_PIPELINE_EXECUTION)
    def mutate(
        self, graphene_info: ResolveInfo, executionParams: GrapheneExecutionParams
    ) -> Union[GrapheneLaunchRunSuccess, GrapheneError, GraphenePythonError]:
        return create_execution_params_and_launch_pipeline_exec(graphene_info, executionParams)


class GrapheneLaunchMultipleRunsMutation(graphene.Mutation):
    """Launches multiple job runs."""

    Output = graphene.NonNull(GrapheneLaunchMultipleRunsResultOrError)

    class Arguments:
        executionParamsList = non_null_list(GrapheneExecutionParams)

    class Meta:
        name = "LaunchMultipleRunsMutation"

    @capture_error
    def mutate(
        self, graphene_info: ResolveInfo, executionParamsList: list[GrapheneExecutionParams]
    ) -> Union[
        GrapheneLaunchMultipleRunsResult,
        GrapheneError,
        GraphenePythonError,
    ]:
        launch_multiple_runs_result = []

        for execution_params in executionParamsList:
            result = GrapheneLaunchRunMutation.mutate(
                None, graphene_info, executionParams=execution_params
            )
            launch_multiple_runs_result.append(result)

        return GrapheneLaunchMultipleRunsResult(
            launchMultipleRunsResult=launch_multiple_runs_result
        )


class GrapheneLaunchBackfillMutation(graphene.Mutation):
    """Launches a set of partition backfill runs."""

    Output = graphene.NonNull(GrapheneLaunchBackfillResult)

    class Arguments:
        backfillParams = graphene.NonNull(GrapheneLaunchBackfillParams)

    class Meta:
        name = "LaunchBackfillMutation"

    @capture_error
    @require_permission_check(Permissions.LAUNCH_PARTITION_BACKFILL)
    def mutate(self, graphene_info: ResolveInfo, backfillParams: GrapheneLaunchBackfillParams):
        return create_and_launch_partition_backfill(graphene_info, backfillParams)


class GrapheneCancelBackfillMutation(graphene.Mutation):
    """Cancels a set of partition backfill runs."""

    Output = graphene.NonNull(GrapheneCancelBackfillResult)

    class Arguments:
        backfillId = graphene.NonNull(graphene.String)

    class Meta:
        name = "CancelBackfillMutation"

    @capture_error
    @require_permission_check(Permissions.CANCEL_PARTITION_BACKFILL)
    def mutate(self, graphene_info: ResolveInfo, backfillId: str):
        return cancel_partition_backfill(graphene_info, backfillId)


class GrapheneResumeBackfillMutation(graphene.Mutation):
    """Resumes a set of partition backfill runs. Resuming a backfill will not retry any failed runs."""

    Output = graphene.NonNull(GrapheneResumeBackfillResult)

    class Arguments:
        backfillId = graphene.NonNull(graphene.String)

    class Meta:
        name = "ResumeBackfillMutation"

    @capture_error
    @require_permission_check(Permissions.LAUNCH_PARTITION_BACKFILL)
    def mutate(self, graphene_info: ResolveInfo, backfillId: str):
        return resume_partition_backfill(graphene_info, backfillId)


class GrapheneReexecuteBackfillMutation(graphene.Mutation):
    """Retries a set of partition backfill runs. Retrying a backfill will create a new backfill to retry any failed partitions."""

    Output = graphene.NonNull(GrapheneLaunchBackfillResult)

    class Arguments:
        reexecutionParams = graphene.Argument(GrapheneReexecutionParams)

    class Meta:
        name = "RetryBackfillMutation"

    @capture_error
    @require_permission_check(Permissions.LAUNCH_PARTITION_BACKFILL)
    def mutate(
        self,
        graphene_info: ResolveInfo,
        reexecutionParams: GrapheneReexecutionParams,
    ):
        return retry_partition_backfill(
            graphene_info,
            backfill_id=reexecutionParams["parentRunId"],
            strategy=reexecutionParams["strategy"],
        )


class GrapheneAddDynamicPartitionMutation(graphene.Mutation):
    """Adds a partition to a dynamic partition set."""

    Output = graphene.NonNull(GrapheneAddDynamicPartitionResult)

    class Arguments:
        repositorySelector = graphene.NonNull(GrapheneRepositorySelector)
        partitionsDefName = graphene.NonNull(graphene.String)
        partitionKey = graphene.NonNull(graphene.String)

    class Meta:
        name = "AddDynamicPartitionMutation"

    @capture_error
    @require_permission_check(Permissions.EDIT_DYNAMIC_PARTITIONS)
    def mutate(
        self,
        graphene_info: ResolveInfo,
        repositorySelector: GrapheneRepositorySelector,
        partitionsDefName: str,
        partitionKey: str,
    ):
        return add_dynamic_partition(
            graphene_info, repositorySelector, partitionsDefName, partitionKey
        )


class GrapheneDeleteDynamicPartitionsMutation(graphene.Mutation):
    """Deletes partitions from a dynamic partition set."""

    Output = graphene.NonNull(GrapheneDeleteDynamicPartitionsResult)

    class Arguments:
        repositorySelector = graphene.NonNull(GrapheneRepositorySelector)
        partitionsDefName = graphene.NonNull(graphene.String)
        partitionKeys = non_null_list(graphene.String)

    class Meta:
        name = "DeleteDynamicPartitionsMutation"

    @capture_error
    @require_permission_check(Permissions.EDIT_DYNAMIC_PARTITIONS)
    def mutate(
        self,
        graphene_info: ResolveInfo,
        repositorySelector: GrapheneRepositorySelector,
        partitionsDefName: str,
        partitionKeys: Sequence[str],
    ):
        return delete_dynamic_partitions(
            graphene_info, repositorySelector, partitionsDefName, partitionKeys
        )


def create_execution_params_and_launch_pipeline_reexec(graphene_info, execution_params_dict):
    execution_params = create_execution_params(graphene_info, execution_params_dict)
    assert_permission_for_location(
        graphene_info,
        Permissions.LAUNCH_PIPELINE_REEXECUTION,
        execution_params.selector.location_name,
    )
    return launch_pipeline_reexecution(graphene_info, execution_params=execution_params)


class GrapheneLaunchRunReexecutionMutation(graphene.Mutation):
    """Re-executes a job run."""

    Output = graphene.NonNull(GrapheneLaunchRunReexecutionResult)

    class Arguments:
        executionParams = graphene.Argument(GrapheneExecutionParams)
        reexecutionParams = graphene.Argument(GrapheneReexecutionParams)

    class Meta:
        name = "LaunchRunReexecutionMutation"

    @capture_error
    @require_permission_check(Permissions.LAUNCH_PIPELINE_REEXECUTION)
    def mutate(
        self,
        graphene_info: ResolveInfo,
        executionParams: Optional[GrapheneExecutionParams] = None,
        reexecutionParams: Optional[GrapheneReexecutionParams] = None,
    ):
        if bool(executionParams) == bool(reexecutionParams):
            raise DagsterInvariantViolationError(
                "Must only provide one of either executionParams or reexecutionParams"
            )

        if executionParams:
            return create_execution_params_and_launch_pipeline_reexec(
                graphene_info,
                execution_params_dict=executionParams,
            )
        elif reexecutionParams:
            extra_tags = None
            if reexecutionParams.get("extraTags"):
                extra_tags = {t["key"]: t["value"] for t in reexecutionParams["extraTags"]}

            use_parent_run_tags = None
            if reexecutionParams.get("useParentRunTags") is not None:
                use_parent_run_tags = reexecutionParams["useParentRunTags"]

            return launch_reexecution_from_parent_run(
                graphene_info,
                parent_run_id=reexecutionParams["parentRunId"],
                strategy=reexecutionParams["strategy"],
                extra_tags=extra_tags,
                use_parent_run_tags=use_parent_run_tags,
            )
        else:
            check.failed("Unreachable")


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
    @require_permission_check(Permissions.TERMINATE_PIPELINE_EXECUTION)
    def mutate(
        self,
        graphene_info: ResolveInfo,
        runId: str,
        terminatePolicy: Optional[GrapheneTerminateRunPolicy] = None,
    ):
        return terminate_pipeline_execution(
            graphene_info,
            runId,
            terminatePolicy or GrapheneTerminateRunPolicy.SAFE_TERMINATE,
        )


class GrapheneTerminateRunsMutation(graphene.Mutation):
    """Terminates a set of runs given their run IDs."""

    Output = graphene.NonNull(GrapheneTerminateRunsResultOrError)

    class Arguments:
        runIds = non_null_list(graphene.String)
        terminatePolicy = graphene.Argument(GrapheneTerminateRunPolicy)

    class Meta:
        name = "TerminateRunsMutation"

    @capture_error
    @require_permission_check(Permissions.TERMINATE_PIPELINE_EXECUTION)
    def mutate(
        self,
        graphene_info: ResolveInfo,
        runIds: Sequence[str],
        terminatePolicy: Optional[GrapheneTerminateRunPolicy] = None,
    ):
        return terminate_pipeline_execution_for_runs(
            graphene_info,
            runIds,
            terminatePolicy or GrapheneTerminateRunPolicy.SAFE_TERMINATE,
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
    @require_permission_check(Permissions.RELOAD_REPOSITORY_LOCATION)
    def mutate(
        self, graphene_info: ResolveInfo, repositoryLocationName: str
    ) -> Union[
        GrapheneWorkspaceLocationEntry,
        GrapheneReloadNotSupported,
        GrapheneRepositoryLocationNotFound,
    ]:
        assert_permission_for_location(
            graphene_info, Permissions.RELOAD_REPOSITORY_LOCATION, repositoryLocationName
        )

        if not graphene_info.context.has_code_location_name(repositoryLocationName):
            return GrapheneRepositoryLocationNotFound(repositoryLocationName)

        if not graphene_info.context.is_reload_supported(repositoryLocationName):
            return GrapheneReloadNotSupported(repositoryLocationName)

        # The current workspace context is a WorkspaceRequestContext, which contains a reference to the
        # repository locations that were present in the root IWorkspaceProcessContext the start of the
        # request. Reloading a repository location modifies the IWorkspaceProcessContext, rendeirng
        # our current WorkspaceRequestContext outdated. Therefore, `reload_repository_location` returns
        # an updated WorkspaceRequestContext for us to use.
        new_context = graphene_info.context.reload_code_location(repositoryLocationName)
        return GrapheneWorkspaceLocationEntry(
            check.not_none(new_context.get_location_entry(repositoryLocationName))
        )


class GrapheneShutdownRepositoryLocationMutation(graphene.Mutation):
    """Shuts down a code location server."""

    Output = graphene.NonNull(GrapheneShutdownRepositoryLocationMutationResult)

    class Arguments:
        repositoryLocationName = graphene.NonNull(graphene.String)

    class Meta:
        name = "ShutdownRepositoryLocationMutation"

    @capture_error
    @require_permission_check(Permissions.RELOAD_REPOSITORY_LOCATION)
    def mutate(
        self, graphene_info: ResolveInfo, repositoryLocationName: str
    ) -> Union[GrapheneRepositoryLocationNotFound, GrapheneShutdownRepositoryLocationSuccess]:
        assert_permission_for_location(
            graphene_info, Permissions.RELOAD_REPOSITORY_LOCATION, repositoryLocationName
        )
        if not graphene_info.context.has_code_location_name(repositoryLocationName):
            return GrapheneRepositoryLocationNotFound(repositoryLocationName)

        if not graphene_info.context.is_shutdown_supported(repositoryLocationName):
            raise Exception(
                f"Location {repositoryLocationName} does not support shutting down via GraphQL"
            )

        graphene_info.context.shutdown_code_location(repositoryLocationName)
        return GrapheneShutdownRepositoryLocationSuccess(
            repositoryLocationName=repositoryLocationName
        )


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
    def mutate(self, graphene_info: ResolveInfo):
        new_context = graphene_info.context.reload_workspace()
        return fetch_workspace(new_context)


class GrapheneAssetWipeSuccess(graphene.ObjectType):
    """Output indicating that asset history was deleted."""

    assetPartitionRanges = non_null_list(GrapheneAssetPartitionRange)

    class Meta:
        name = "AssetWipeSuccess"


class GrapheneAssetWipeMutationResult(graphene.Union):
    """The output from deleting asset history."""

    class Meta:
        types = (
            GrapheneAssetNotFoundError,
            GrapheneUnauthorizedError,
            GraphenePythonError,
            GrapheneUnsupportedOperationError,
            GrapheneAssetWipeSuccess,
        )
        name = "AssetWipeMutationResult"


class GrapheneAssetWipeMutation(graphene.Mutation):
    """Deletes asset history from storage."""

    Output = graphene.NonNull(GrapheneAssetWipeMutationResult)

    class Arguments:
        assetPartitionRanges = graphene.Argument(non_null_list(GraphenePartitionsByAssetSelector))

    class Meta:
        name = "AssetWipeMutation"

    @capture_error
    @check_permission(Permissions.WIPE_ASSETS)
    def mutate(
        self,
        graphene_info: ResolveInfo,
        assetPartitionRanges: Sequence[GraphenePartitionsByAssetSelector],
    ) -> GrapheneAssetWipeMutationResult:
        normalized_ranges = [
            AssetPartitionWipeRange(
                AssetKey.from_graphql_input(ap.assetKey),
                PartitionKeyRange(start=ap.partitions.range.start, end=ap.partitions.range.end)
                if ap.partitions
                else None,
            )
            for ap in assetPartitionRanges
        ]

        return wipe_assets(graphene_info, normalized_ranges)


class GrapheneReportRunlessAssetEventsSuccess(graphene.ObjectType):
    """Output indicating that runless asset events were reported."""

    assetKey = graphene.NonNull(GrapheneAssetKey)

    class Meta:
        name = "ReportRunlessAssetEventsSuccess"


class GrapheneReportRunlessAssetEventsResult(graphene.Union):
    """The output from reporting runless events."""

    class Meta:
        types = (
            GrapheneUnauthorizedError,
            GraphenePythonError,
            GrapheneReportRunlessAssetEventsSuccess,
        )
        name = "ReportRunlessAssetEventsResult"


class GrapheneReportRunlessAssetEventsMutation(graphene.Mutation):
    """Reports runless events for an asset or a subset of its partitions."""

    Output = graphene.NonNull(GrapheneReportRunlessAssetEventsResult)

    class Arguments:
        eventParams = graphene.Argument(graphene.NonNull(GrapheneReportRunlessAssetEventsParams))

    class Meta:
        name = "ReportRunlessAssetEventsMutation"

    @capture_error
    @require_permission_check(Permissions.REPORT_RUNLESS_ASSET_EVENTS)
    def mutate(
        self, graphene_info: ResolveInfo, eventParams: GrapheneReportRunlessAssetEventsParams
    ):
        event_type = eventParams["eventType"].to_dagster_event_type()
        asset_key = AssetKey.from_graphql_input(eventParams["assetKey"])
        partition_keys = eventParams.get("partitionKeys", None)
        description = eventParams.get("description", None)

        reporting_user_tags = {**graphene_info.context.get_reporting_user_tags()}

        asset_graph = graphene_info.context.asset_graph

        assert_permission_for_asset_graph(
            graphene_info, asset_graph, [asset_key], Permissions.REPORT_RUNLESS_ASSET_EVENTS
        )

        return report_runless_asset_events(
            graphene_info,
            event_type=event_type,
            asset_key=asset_key,
            partition_keys=partition_keys,
            description=description,
            tags=reporting_user_tags,
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
        clientId = graphene.Argument(graphene.NonNull(graphene.String))
        metadata = graphene.Argument(graphene.NonNull(graphene.String))

    class Meta:
        name = "LogTelemetryMutation"

    @capture_error
    def mutate(
        self, graphene_info: ResolveInfo, action: str, clientTime: str, clientId: str, metadata: str
    ):
        action = log_ui_telemetry_event(
            graphene_info,
            action=action,
            client_time=clientTime,
            client_id=clientId,
            metadata=metadata,
        )
        return action


class GrapheneSetNuxSeenMutation(graphene.Mutation):
    """Store whether we've shown the nux to any user and they've dismissed or submitted it."""

    Output = graphene.NonNull(graphene.Boolean)

    class Meta:
        name = "SetNuxSeenMutation"

    @capture_error
    def mutate(self, _graphene_info):
        set_nux_seen()
        return get_has_seen_nux()


class GrapheneSetAutoMaterializePausedMutation(graphene.Mutation):
    """Toggle asset auto materializing on or off."""

    Output = graphene.NonNull(graphene.Boolean)

    class Meta:
        name = "SetAutoMaterializedPausedMutation"

    class Arguments:
        paused = graphene.Argument(graphene.NonNull(graphene.Boolean))

    @capture_error
    @check_permission(Permissions.TOGGLE_AUTO_MATERIALIZE)
    def mutate(self, graphene_info, paused: bool):
        set_auto_materialize_paused(graphene_info.context.instance, paused)
        return paused


class GrapheneSetConcurrencyLimitMutation(graphene.Mutation):
    """Sets the concurrency limit for a given concurrency key."""

    Output = graphene.NonNull(graphene.Boolean)

    class Meta:
        name = "SetConcurrencyLimitMutation"

    class Arguments:
        concurrencyKey = graphene.Argument(graphene.NonNull(graphene.String))
        limit = graphene.Argument(graphene.NonNull(graphene.Int))

    @capture_error
    @check_permission(Permissions.EDIT_CONCURRENCY_LIMIT)
    def mutate(self, graphene_info, concurrencyKey: str, limit: int):
        graphene_info.context.instance.event_log_storage.set_concurrency_slots(
            concurrencyKey, limit
        )
        return True


class GrapheneDeleteConcurrencyLimitMutation(graphene.Mutation):
    """Sets the concurrency limit for a given concurrency key."""

    Output = graphene.NonNull(graphene.Boolean)

    class Meta:
        name = "DeleteConcurrencyLimitMutation"

    class Arguments:
        concurrencyKey = graphene.Argument(graphene.NonNull(graphene.String))

    @capture_error
    @check_permission(Permissions.EDIT_CONCURRENCY_LIMIT)
    def mutate(self, graphene_info, concurrencyKey: str):
        graphene_info.context.instance.event_log_storage.delete_concurrency_limit(concurrencyKey)
        return True


class GrapheneFreeConcurrencySlotsMutation(graphene.Mutation):
    """Frees concurrency slots."""

    Output = graphene.NonNull(graphene.Boolean)

    class Meta:
        name = "FreeConcurrencySlotsMutation"

    class Arguments:
        runId = graphene.Argument(graphene.NonNull(graphene.String))
        stepKey = graphene.Argument(graphene.String)

    @capture_error
    @check_permission(Permissions.EDIT_CONCURRENCY_LIMIT)
    def mutate(self, graphene_info, runId: str, stepKey: Optional[str] = None):
        event_log_storage = graphene_info.context.instance.event_log_storage
        if stepKey:
            event_log_storage.free_concurrency_slot_for_step(runId, stepKey)
        else:
            event_log_storage.free_concurrency_slots_for_run(runId)
        return True


class GrapheneFreeConcurrencySlotsForRunMutation(graphene.Mutation):
    """Frees the concurrency slots occupied by a specific run."""

    Output = graphene.NonNull(graphene.Boolean)

    class Meta:
        name = "FreeConcurrencySlotsForRunMutation"

    class Arguments:
        runId = graphene.Argument(graphene.NonNull(graphene.String))

    @capture_error
    @check_permission(Permissions.EDIT_CONCURRENCY_LIMIT)
    def mutate(self, graphene_info, runId: str):
        graphene_info.context.instance.event_log_storage.free_concurrency_slots_for_run(runId)
        return True


class GrapheneMutation(graphene.ObjectType):
    """The root for all mutations to modify data in your Dagster instance."""

    class Meta:
        name = "Mutation"

    launchPipelineExecution = GrapheneLaunchRunMutation.Field()
    launchRun = GrapheneLaunchRunMutation.Field()
    launchMultipleRuns = GrapheneLaunchMultipleRunsMutation.Field()
    launchPipelineReexecution = GrapheneLaunchRunReexecutionMutation.Field()
    launchRunReexecution = GrapheneLaunchRunReexecutionMutation.Field()
    startSchedule = GrapheneStartScheduleMutation.Field()
    stopRunningSchedule = GrapheneStopRunningScheduleMutation.Field()
    resetSchedule = GrapheneResetScheduleMutation.Field()
    startSensor = GrapheneStartSensorMutation.Field()
    setSensorCursor = GrapheneSetSensorCursorMutation.Field()
    stopSensor = GrapheneStopSensorMutation.Field()
    resetSensor = GrapheneResetSensorMutation.Field()
    sensorDryRun = GrapheneSensorDryRunMutation.Field()
    scheduleDryRun = GrapheneScheduleDryRunMutation.Field()
    terminatePipelineExecution = GrapheneTerminateRunMutation.Field()
    terminateRun = GrapheneTerminateRunMutation.Field()
    terminateRuns = GrapheneTerminateRunsMutation.Field()
    deletePipelineRun = GrapheneDeleteRunMutation.Field()
    deleteRun = GrapheneDeleteRunMutation.Field()
    reloadRepositoryLocation = GrapheneReloadRepositoryLocationMutation.Field()
    reloadWorkspace = GrapheneReloadWorkspaceMutation.Field()
    shutdownRepositoryLocation = GrapheneShutdownRepositoryLocationMutation.Field()
    wipeAssets = GrapheneAssetWipeMutation.Field()
    reportRunlessAssetEvents = GrapheneReportRunlessAssetEventsMutation.Field()
    launchPartitionBackfill = GrapheneLaunchBackfillMutation.Field()
    resumePartitionBackfill = GrapheneResumeBackfillMutation.Field()
    reexecutePartitionBackfill = GrapheneReexecuteBackfillMutation.Field()
    cancelPartitionBackfill = GrapheneCancelBackfillMutation.Field()
    logTelemetry = GrapheneLogTelemetryMutation.Field()
    setNuxSeen = GrapheneSetNuxSeenMutation.Field()
    addDynamicPartition = GrapheneAddDynamicPartitionMutation.Field()
    deleteDynamicPartitions = GrapheneDeleteDynamicPartitionsMutation.Field()
    setAutoMaterializePaused = GrapheneSetAutoMaterializePausedMutation.Field()
    setConcurrencyLimit = GrapheneSetConcurrencyLimitMutation.Field()
    deleteConcurrencyLimit = GrapheneDeleteConcurrencyLimitMutation.Field()
    freeConcurrencySlotsForRun = GrapheneFreeConcurrencySlotsForRunMutation.Field()
    freeConcurrencySlots = GrapheneFreeConcurrencySlotsMutation.Field()
