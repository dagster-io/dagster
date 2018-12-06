from __future__ import absolute_import
import graphene
from graphene.types.generic import GenericScalar

from dagit.schema import model, errors, pipelines, execution, runs, generic
from .utils import non_null_list


def create_schema():
    return graphene.Schema(
        query=Query,
        mutation=Mutation,
        subscription=Subscription,
        types=[
            pipelines.RegularType,
            pipelines.CompositeType,
            errors.RuntimeMismatchConfigError,
            errors.MissingFieldConfigError,
            errors.FieldNotDefinedConfigError,
            errors.SelectorTypeConfigError,
        ]
    )


class Query(graphene.ObjectType):
    pipelineOrError = graphene.Field(
        lambda: graphene.NonNull(errors.PipelineOrError), name=graphene.NonNull(graphene.String)
    )
    pipeline = graphene.Field(
        lambda: graphene.NonNull(pipelines.Pipeline), name=graphene.NonNull(graphene.String)
    )
    pipelinesOrError = graphene.NonNull(errors.PipelinesOrError)
    pipelines = graphene.Field(lambda: graphene.NonNull(pipelines.PipelineConnection))

    type = graphene.Field(
        lambda: pipelines.Type,
        pipelineName=graphene.NonNull(graphene.String),
        typeName=graphene.NonNull(graphene.String),
    )

    pipelineRuns = non_null_list(lambda: runs.PipelineRun)
    pipelineRun = graphene.Field(lambda: runs.PipelineRun, runId=graphene.NonNull(graphene.ID))

    isPipelineConfigValid = graphene.Field(
        graphene.NonNull(lambda: errors.PipelineConfigValidationResult),
        args={
            'executionParams': graphene.Argument(graphene.NonNull(lambda: PipelineExecutionParams))
        },
    )

    executionPlan = graphene.Field(
        graphene.NonNull(lambda: errors.ExecutionPlanResult),
        args={
            'executionParams': graphene.Argument(graphene.NonNull(lambda: PipelineExecutionParams))
        },
    )

    def resolve_pipelineOrError(self, info, name):
        return model.get_pipeline(info.context, name)

    def resolve_pipeline(self, info, name):
        return model.get_pipeline_or_raise(info.context, name)

    def resolve_pipelinesOrError(self, info):
        return model.get_pipelines(info.context)

    def resolve_pipelines(self, info):
        return model.get_pipelines_or_raise(info.context)

    def resolve_type(self, info, pipelineName, typeName):
        return model.get_pipeline_type(info.context, pipelineName, typeName)

    def resolve_pipelineRuns(self, info):
        return model.get_runs(info.context)

    def resolve_pipelineRun(self, info, runId):
        return model.get_run(info.context, runId)

    def resolve_isPipelineConfigValid(self, info, executionParams):
        return model.validate_pipeline_config(info.context, **executionParams)

    def resolve_executionPlan(self, info, executionParams):
        return model.get_execution_plan(info.context, **executionParams)


class StartPipelineExecutionMutation(graphene.Mutation):
    class Arguments:
        executionParams = graphene.NonNull(lambda: PipelineExecutionParams)

    Output = graphene.NonNull(lambda: errors.StartPipelineExecutionResult)

    def mutate(self, info, executionParams):
        print('STARTING PIPELINE EXECUTION')
        return model.start_pipeline_execution(info.context, **executionParams)


class Mutation(graphene.ObjectType):
    start_pipeline_execution = StartPipelineExecutionMutation.Field()


class Subscription(graphene.ObjectType):
    pipelineRunLogs = graphene.Field(
        graphene.NonNull(lambda: runs.PipelineRunEvent),
        runId=graphene.Argument(graphene.NonNull(graphene.ID)),
        after=graphene.Argument(generic.Cursor)
    )

    def resolve_pipelineRunLogs(self, info, runId, after=None):
        return model.get_pipeline_run_observable(info.context, runId, after)


class PipelineExecutionParams(graphene.InputObjectType):
    pipelineName = graphene.NonNull(graphene.String)
    config = graphene.Field(lambda: PipelineConfig)


class PipelineConfig(GenericScalar):
    class Meta:
        description = '''This type is used when passing in a configuration object
        for pipeline configuration. This is any-typed in the GraphQL type system,
        but must conform to the constraints of the dagster config type system'''
