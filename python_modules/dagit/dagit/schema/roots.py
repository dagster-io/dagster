from dagit.schema import dauphene
from dagit.schema import model


class Query(dauphene.ObjectType):
    pipelineOrError = dauphene.Field(
        dauphene.NonNull('PipelineOrError'), name=dauphene.NonNull(dauphene.String)
    )
    pipeline = dauphene.Field(dauphene.NonNull('Pipeline'), name=dauphene.NonNull(dauphene.String))
    pipelinesOrError = dauphene.NonNull('PipelinesOrError')
    pipelines = dauphene.Field(dauphene.NonNull('PipelineConnection'))

    type = dauphene.Field(
        'Type',
        pipelineName=dauphene.NonNull(dauphene.String),
        typeName=dauphene.NonNull(dauphene.String),
    )

    pipelineRuns = dauphene.non_null_list('PipelineRun')
    pipelineRun = dauphene.Field('PipelineRun', runId=dauphene.NonNull(dauphene.ID))

    isPipelineConfigValid = dauphene.Field(
        dauphene.NonNull('PipelineConfigValidationResult'),
        args={'executionParams': dauphene.Argument(dauphene.NonNull('PipelineExecutionParams'))},
    )

    executionPlan = dauphene.Field(
        dauphene.NonNull('ExecutionPlanResult'),
        args={'executionParams': dauphene.Argument(dauphene.NonNull('PipelineExecutionParams'))},
    )

    def resolve_pipelineOrError(self, info, name):
        return model.get_pipeline(info, name)

    def resolve_pipeline(self, info, name):
        return model.get_pipeline_or_raise(info, name)

    def resolve_pipelinesOrError(self, info):
        return model.get_pipelines(info)

    def resolve_pipelines(self, info):
        return model.get_pipelines_or_raise(info)

    def resolve_type(self, info, pipelineName, typeName):
        return model.get_pipeline_type(info, pipelineName, typeName)

    def resolve_pipelineRuns(self, info):
        return model.get_runs(info)

    def resolve_pipelineRun(self, info, runId):
        return model.get_run(info, runId)

    def resolve_isPipelineConfigValid(self, info, executionParams):
        return model.validate_pipeline_config(info, **executionParams)

    def resolve_executionPlan(self, info, executionParams):
        return model.get_execution_plan(info, **executionParams)


class StartPipelineExecutionMutation(dauphene.Mutation):
    class Arguments:
        executionParams = dauphene.NonNull('PipelineExecutionParams')

    Output = dauphene.NonNull('StartPipelineExecutionResult')

    def mutate(self, info, executionParams):
        return model.start_pipeline_execution(info, **executionParams)


class Mutation(dauphene.ObjectType):
    start_pipeline_execution = StartPipelineExecutionMutation.Field()


class Subscription(dauphene.ObjectType):
    pipelineRunLogs = dauphene.Field(
        dauphene.NonNull('PipelineRunEvent'),
        runId=dauphene.Argument(dauphene.NonNull(dauphene.ID)),
        after=dauphene.Argument('Cursor')
    )

    def resolve_pipelineRunLogs(self, info, runId, after=None):
        return model.get_pipeline_run_observable(info, runId, after)


class PipelineExecutionParams(dauphene.InputObjectType):
    pipelineName = dauphene.NonNull(dauphene.String)
    config = dauphene.Field('PipelineConfig')


class PipelineConfig(dauphene.GenericScalar, dauphene.Scalar):
    class Meta:
        description = '''This type is used when passing in a configuration object
        for pipeline configuration. This is any-typed in the GraphQL type system,
        but must conform to the constraints of the dagster config type system'''
