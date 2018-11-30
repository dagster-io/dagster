import graphene
from graphene.types.generic import GenericScalar

from . import model, errors, pipeline, execution, run
from .utils import non_null_list


def create_schema():
    return graphene.Schema(
        query=Query,
        mutation=Mutation,
        subscription=Subscription,
        types=[
            pipeline.RegularType,
            pipeline.CompositeType,
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
    pipelinesOrError = graphene.NonNull(errors.PipelinesOrError)

    type = graphene.Field(
        lambda: pipeline.Type,
        pipelineName=graphene.NonNull(graphene.String),
        typeName=graphene.NonNull(graphene.String),
    )

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

    def resolve_pipeline(self, info, name):
        return model.get_pipeline(info.context, name)

    def resolve_pipelines(self, info):
        return model.get_pipelines(info.context)

    def resolve_type(self, info, pipelineName, typeName):
        return model.get_pipeline_type(info.context, pipelineName, typeName)

    def resolve_isPipelineConfigValid(self, info, executionParams):
        return model.validate_pipeline_config(info.context, **executionParams)

    def resolve_executionPlan(self, info, executionParams):
        return model.get_execution_plan(info.context, **executionParams)


class StartPipelineExecutionMutation(graphene.Mutation):
    class Arguments:
        executionParams = graphene.NonNull(lambda: PipelineExecutionParams)

    Output = graphene.NonNull(lambda: errors.StartPipelineExecutionResult)

    def mutate(self, info, executionParams):
        return model.start_pipeline_execution(info.context, **executionParams)


class Mutation(graphene.ObjectType):
    start_pipeline_execution = StartPipelineExecutionMutation.Field()


class Subscription(graphene.ObjectType):
    pipelineRunLogs = graphene.Field(
        graphene.NonNull(lambda: run.PipelineRunEvent),
        runId=graphene.Argument(graphene.NonNull(graphene.ID)),
        after=graphene.Argument(graphene.String)
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
