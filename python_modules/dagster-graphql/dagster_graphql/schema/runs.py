import sys

import dagster._check as check
import graphene
import yaml
from dagster._utils.error import serializable_error_info_from_exc_info
from dagster._utils.yaml_utils import load_run_config_yaml
from graphene.types.generic import GenericScalar

from ..implementation.fetch_runs import get_runs, get_runs_count
from ..implementation.utils import UserFacingGraphQLError
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
    IN_PROGRESS = "IN_PROGRESS"

    class Meta:
        name = "StepEventStatus"


class GrapheneLaunchPipelineRunSuccess(graphene.Interface):
    run = graphene.Field(graphene.NonNull("dagster_graphql.schema.pipelines.pipeline.GrapheneRun"))

    class Meta:
        name = "LaunchPipelineRunSuccess"


class GrapheneLaunchRunSuccess(graphene.ObjectType):
    run = graphene.Field(graphene.NonNull("dagster_graphql.schema.pipelines.pipeline.GrapheneRun"))

    class Meta:
        interfaces = (GrapheneLaunchPipelineRunSuccess,)
        name = "LaunchRunSuccess"


class GrapheneRunGroup(graphene.ObjectType):
    rootRunId = graphene.NonNull(graphene.String)
    runs = graphene.List("dagster_graphql.schema.pipelines.pipeline.GrapheneRun")

    class Meta:
        name = "RunGroup"

    def __init__(self, root_run_id, runs):
        from .pipelines.pipeline import GrapheneRun

        check.str_param(root_run_id, "root_run_id")
        check.list_param(runs, "runs", GrapheneRun)

        super().__init__(rootRunId=root_run_id, runs=runs)


class GrapheneRunGroups(graphene.ObjectType):
    results = non_null_list(GrapheneRunGroup)

    class Meta:
        name = "RunGroups"


launch_pipeline_run_result_types = (GrapheneLaunchRunSuccess,)


class GrapheneLaunchRunResult(graphene.Union):
    class Meta:
        from .backfill import pipeline_execution_error_types

        types = launch_pipeline_run_result_types + pipeline_execution_error_types

        name = "LaunchRunResult"


class GrapheneLaunchRunReexecutionResult(graphene.Union):
    class Meta:
        from .backfill import pipeline_execution_error_types

        types = launch_pipeline_run_result_types + pipeline_execution_error_types

        name = "LaunchRunReexecutionResult"


class GraphenePipelineRuns(graphene.Interface):
    results = non_null_list("dagster_graphql.schema.pipelines.pipeline.GrapheneRun")
    count = graphene.Int()

    class Meta:
        name = "PipelineRuns"


class GrapheneRuns(graphene.ObjectType):
    results = non_null_list("dagster_graphql.schema.pipelines.pipeline.GrapheneRun")
    count = graphene.Int()

    class Meta:
        interfaces = (GraphenePipelineRuns,)
        name = "Runs"

    def __init__(self, filters, cursor, limit):
        super().__init__()

        self._filters = filters
        self._cursor = cursor
        self._limit = limit

    def resolve_results(self, graphene_info):
        return get_runs(graphene_info, self._filters, self._cursor, self._limit)

    def resolve_count(self, graphene_info):
        return get_runs_count(graphene_info, self._filters)


class GrapheneRunsOrError(graphene.Union):
    class Meta:
        types = (GrapheneRuns, GrapheneInvalidPipelineRunsFilterError, GraphenePythonError)
        name = "RunsOrError"


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
        for pipeline configuration. Can either be passed in as a string (the
        YAML configuration object) or as the configuration object itself. In
        either case, the object must conform to the constraints of the dagster config type system.
        """
        name = "RunConfigData"


def parse_run_config_input(run_config, raise_on_error: bool):
    if run_config and isinstance(run_config, str):
        try:
            return load_run_config_yaml(run_config)
        except yaml.YAMLError:
            if raise_on_error:
                raise UserFacingGraphQLError(
                    GraphenePythonError(serializable_error_info_from_exc_info(sys.exc_info()))
                )
            # Pass the config through as a string so that it will return a useful validation error
            return run_config
    return run_config


types = [
    GrapheneLaunchRunResult,
    GrapheneLaunchRunReexecutionResult,
    GrapheneLaunchPipelineRunSuccess,
    GrapheneLaunchRunSuccess,
    GrapheneRunsOrError,
    GrapheneRunConfigData,
    GrapheneRunGroup,
    GrapheneRunGroupOrError,
    GrapheneRunGroups,
    GrapheneRunGroupsOrError,
]
