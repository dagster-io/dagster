import graphene
from dagster import check
from graphene.types.generic import GenericScalar

from ..implementation.fetch_runs import get_runs, get_runs_count
from .errors import (
    GrapheneInvalidPipelineRunsFilterError,
    GraphenePythonError,
    GrapheneRunGroupNotFoundError,
)
from .util import non_null_list


class GrapheneStepEventStatus(graphene.Enum):
    SKIPPED = "SKIPPED"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"

    class Meta:
        name = "StepEventStatus"


class GrapheneLaunchPipelineRunSuccess(graphene.ObjectType):
    run = graphene.Field(
        graphene.NonNull("dagster_graphql.schema.pipelines.pipeline.GraphenePipelineRun")
    )

    class Meta:
        name = "LaunchPipelineRunSuccess"


class GrapheneRunGroup(graphene.ObjectType):
    rootRunId = graphene.NonNull(graphene.String)
    runs = graphene.List("dagster_graphql.schema.pipelines.pipeline.GraphenePipelineRun")

    class Meta:
        name = "RunGroup"

    def __init__(self, root_run_id, runs):
        from .pipelines.pipeline import GraphenePipelineRun

        check.str_param(root_run_id, "root_run_id")
        check.list_param(runs, "runs", GraphenePipelineRun)

        super().__init__(rootRunId=root_run_id, runs=runs)


class GrapheneRunGroups(graphene.ObjectType):
    results = non_null_list(GrapheneRunGroup)

    class Meta:
        name = "RunGroups"


launch_pipeline_run_result_types = (GrapheneLaunchPipelineRunSuccess,)


class GrapheneLaunchPipelineExecutionResult(graphene.Union):
    class Meta:
        from .backfill import pipeline_execution_error_types

        types = launch_pipeline_run_result_types + pipeline_execution_error_types

        name = "LaunchPipelineExecutionResult"


class GrapheneLaunchPipelineReexecutionResult(graphene.Union):
    class Meta:
        from .backfill import pipeline_execution_error_types

        types = launch_pipeline_run_result_types + pipeline_execution_error_types

        name = "LaunchPipelineReexecutionResult"


class GraphenePipelineRuns(graphene.ObjectType):
    results = non_null_list("dagster_graphql.schema.pipelines.pipeline.GraphenePipelineRun")
    count = graphene.Int()

    class Meta:
        name = "PipelineRuns"

    def __init__(self, filters, cursor, limit):
        super().__init__()

        self._filters = filters
        self._cursor = cursor
        self._limit = limit

    def resolve_results(self, graphene_info):
        return get_runs(graphene_info, self._filters, self._cursor, self._limit)

    def resolve_count(self, graphene_info):
        return get_runs_count(graphene_info, self._filters)


class GraphenePipelineRunsOrError(graphene.Union):
    class Meta:
        types = (GraphenePipelineRuns, GrapheneInvalidPipelineRunsFilterError, GraphenePythonError)
        name = "PipelineRunsOrError"


class GrapheneRunGroupOrError(graphene.Union):
    class Meta:
        types = (GrapheneRunGroup, GrapheneRunGroupNotFoundError, GraphenePythonError)
        name = "RunGroupOrError"


class GrapheneRunGroupsOrError(graphene.ObjectType):
    results = non_null_list(GrapheneRunGroup)

    class Meta:
        types = (GrapheneRunGroups, GraphenePythonError)
        name = "RunGroupsOrError"


class GrapheneRunConfigData(GenericScalar, graphene.Scalar):
    class Meta:
        description = """This type is used when passing in a configuration object
        for pipeline configuration. This is any-typed in the GraphQL type system,
        but must conform to the constraints of the dagster config type system"""
        name = "RunConfigData"


types = [
    GrapheneLaunchPipelineExecutionResult,
    GrapheneLaunchPipelineReexecutionResult,
    GrapheneLaunchPipelineRunSuccess,
    GraphenePipelineRuns,
    GraphenePipelineRunsOrError,
    GrapheneRunConfigData,
    GrapheneRunGroup,
    GrapheneRunGroupOrError,
    GrapheneRunGroups,
    GrapheneRunGroupsOrError,
]
