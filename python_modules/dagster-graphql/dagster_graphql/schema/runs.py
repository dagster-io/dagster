import graphene
from dagster import check
from graphene.types.generic import GenericScalar

from ..implementation.fetch_runs import get_runs, get_runs_count
from .errors import (
    GrapheneInvalidDagsterRunsFilterError,
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


class GrapheneLaunchDagsterRunSuccess(graphene.ObjectType):
    run = graphene.Field(
        graphene.NonNull("dagster_graphql.schema.pipelines.pipeline.GrapheneDagsterRun")
    )

    class Meta:
        name = "LaunchDagsterRunSuccess"


class GrapheneRunGroup(graphene.ObjectType):
    rootRunId = graphene.NonNull(graphene.String)
    runs = graphene.List("dagster_graphql.schema.pipelines.pipeline.GrapheneDagsterRun")

    class Meta:
        name = "RunGroup"

    def __init__(self, root_run_id, runs):
        from .pipelines.pipeline import GrapheneDagsterRun

        check.str_param(root_run_id, "root_run_id")
        check.list_param(runs, "runs", GrapheneDagsterRun)

        super().__init__(rootRunId=root_run_id, runs=runs)


class GrapheneRunGroups(graphene.ObjectType):
    results = non_null_list(GrapheneRunGroup)

    class Meta:
        name = "RunGroups"


launch_dagster_run_result_types = (GrapheneLaunchDagsterRunSuccess,)


class GrapheneLaunchPipelineExecutionResult(graphene.Union):
    class Meta:
        from .backfill import pipeline_execution_error_types

        types = launch_dagster_run_result_types + pipeline_execution_error_types

        name = "LaunchPipelineExecutionResult"


class GrapheneLaunchPipelineReexecutionResult(graphene.Union):
    class Meta:
        from .backfill import pipeline_execution_error_types

        types = launch_dagster_run_result_types + pipeline_execution_error_types

        name = "LaunchPipelineReexecutionResult"


class GrapheneDagsterRuns(graphene.ObjectType):
    results = non_null_list("dagster_graphql.schema.pipelines.pipeline.GrapheneDagsterRun")
    count = graphene.Int()

    class Meta:
        name = "DagsterRuns"

    def __init__(self, filters, cursor, limit):
        super().__init__()

        self._filters = filters
        self._cursor = cursor
        self._limit = limit

    def resolve_results(self, graphene_info):
        return get_runs(graphene_info, self._filters, self._cursor, self._limit)

    def resolve_count(self, graphene_info):
        return get_runs_count(graphene_info, self._filters)


class GrapheneDagsterRunsOrError(graphene.Union):
    class Meta:
        types = (GrapheneDagsterRuns, GrapheneInvalidDagsterRunsFilterError, GraphenePythonError)
        name = "DagsterRunsOrError"


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
    GrapheneLaunchDagsterRunSuccess,
    GrapheneDagsterRuns,
    GrapheneDagsterRunsOrError,
    GrapheneRunConfigData,
    GrapheneRunGroup,
    GrapheneRunGroupOrError,
    GrapheneRunGroups,
    GrapheneRunGroupsOrError,
]
