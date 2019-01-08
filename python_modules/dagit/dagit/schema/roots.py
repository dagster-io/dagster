from dagit.schema import dauphin
from dagit.schema import model
from ..version import __version__


class DauphinQuery(dauphin.ObjectType):
    class Meta:
        name = 'Query'

    version = dauphin.NonNull(dauphin.String)
    pipelineOrError = dauphin.Field(
        dauphin.NonNull('PipelineOrError'),
        name=dauphin.NonNull(dauphin.String),
        solidSubset=dauphin.Argument(dauphin.List(dauphin.NonNull(dauphin.String)), required=False),
    )
    pipeline = dauphin.Field(
        dauphin.NonNull('Pipeline'),
        name=dauphin.NonNull(dauphin.String),
        solidSubset=dauphin.Argument(dauphin.List(dauphin.NonNull(dauphin.String)), required=False),
    )
    pipelinesOrError = dauphin.NonNull('PipelinesOrError')
    pipelines = dauphin.Field(dauphin.NonNull('PipelineConnection'))

    type = dauphin.Field(
        'Type',
        pipelineName=dauphin.NonNull(dauphin.String),
        typeName=dauphin.Argument(dauphin.NonNull(dauphin.String)),
    )

    pipelineRuns = dauphin.non_null_list('PipelineRun')
    pipelineRun = dauphin.Field('PipelineRun', runId=dauphin.NonNull(dauphin.ID))

    isPipelineConfigValid = dauphin.Field(
        dauphin.NonNull('PipelineConfigValidationResult'),
        args={'executionParams': dauphin.Argument(dauphin.NonNull('PipelineExecutionParams'))},
    )

    executionPlan = dauphin.Field(
        dauphin.NonNull('ExecutionPlanResult'),
        args={'executionParams': dauphin.Argument(dauphin.NonNull('PipelineExecutionParams'))},
    )

    def resolve_version(self, _info):
        return __version__

    def resolve_pipelineOrError(self, info, **kwargs):
        return model.get_pipeline(info, kwargs['name'], kwargs.get('solidSubset'))

    def resolve_pipeline(self, info, **kwargs):
        return model.get_pipeline_or_raise(info, kwargs['name'], kwargs.get('solidSubset'))

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


class StartPipelineExecutionMutation(dauphin.Mutation):
    class Meta:
        name = 'StartPipelineExecutionMutation'

    class Arguments:
        executionParams = dauphin.NonNull('PipelineExecutionParams')

    Output = dauphin.NonNull('StartPipelineExecutionResult')

    def mutate(self, info, executionParams):
        return model.start_pipeline_execution(info, **executionParams)


class DauphinMutation(dauphin.ObjectType):
    class Meta:
        name = 'Mutation'

    start_pipeline_execution = StartPipelineExecutionMutation.Field()


class DauphinSubscription(dauphin.ObjectType):
    class Meta:
        name = 'Subscription'

    pipelineRunLogs = dauphin.Field(
        dauphin.NonNull('PipelineRunLogsSubscriptionPayload'),
        runId=dauphin.Argument(dauphin.NonNull(dauphin.ID)),
        after=dauphin.Argument('Cursor'),
    )

    def resolve_pipelineRunLogs(self, info, runId, after=None):
        return model.get_pipeline_run_observable(info, runId, after)


class DauphinPipelineExecutionParams(dauphin.InputObjectType):
    class Meta:
        name = 'PipelineExecutionParams'

    pipelineName = dauphin.NonNull(dauphin.String)
    config = dauphin.Field('PipelineConfig')


class DauphinPipelineConfig(dauphin.GenericScalar, dauphin.Scalar):
    class Meta:
        name = 'PipelineConfig'
        description = '''This type is used when passing in a configuration object
        for pipeline configuration. This is any-typed in the GraphQL type system,
        but must conform to the constraints of the dagster config type system'''
