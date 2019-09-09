from dagster_graphql import dauphin
from dagster_graphql.implementation.environment_schema import (
    resolve_config_type_or_error,
    resolve_environment_schema_or_error,
    resolve_is_environment_config_valid,
)
from dagster_graphql.implementation.execution import (
    ExecutionMetadata,
    ExecutionParams,
    do_execute_plan,
    get_compute_log_observable,
    get_pipeline_run_observable,
    start_pipeline_execution,
)
from dagster_graphql.implementation.fetch_pipelines import (
    get_dauphin_pipeline_from_selector,
    get_pipeline_or_error,
    get_pipeline_or_raise,
    get_pipelines_or_error,
    get_pipelines_or_raise,
)
from dagster_graphql.implementation.fetch_runs import (
    get_execution_plan,
    get_run,
    get_runs,
    validate_pipeline_config,
)
from dagster_graphql.implementation.fetch_types import get_config_type, get_runtime_type
from dagster_graphql.implementation.utils import UserFacingGraphQLError

from dagster import check
from dagster.core.definitions.pipeline import ExecutionSelector
from dagster.core.instance import DagsterFeatures

from .config_types import to_dauphin_config_type
from .run_schedule import (
    DauphinEndRunningScheduleMutation,
    DauphinStartScheduleMutation,
    get_scheduler_or_error,
    get_schedules,
)


class DauphinQuery(dauphin.ObjectType):
    class Meta:
        name = 'Query'

    version = dauphin.NonNull(dauphin.String)
    pipelineOrError = dauphin.Field(
        dauphin.NonNull('PipelineOrError'), params=dauphin.NonNull('ExecutionSelector')
    )
    pipeline = dauphin.Field(
        dauphin.NonNull('Pipeline'), params=dauphin.NonNull('ExecutionSelector')
    )
    pipelinesOrError = dauphin.NonNull('PipelinesOrError')
    pipelines = dauphin.Field(dauphin.NonNull('PipelineConnection'))

    configTypeOrError = dauphin.Field(
        dauphin.NonNull('ConfigTypeOrError'),
        pipelineName=dauphin.Argument(dauphin.NonNull(dauphin.String)),
        configTypeName=dauphin.Argument(dauphin.NonNull(dauphin.String)),
        mode=dauphin.Argument(dauphin.NonNull(dauphin.String)),
    )

    runtimeTypeOrError = dauphin.Field(
        dauphin.NonNull('RuntimeTypeOrError'),
        pipelineName=dauphin.Argument(dauphin.NonNull(dauphin.String)),
        runtimeTypeName=dauphin.Argument(dauphin.NonNull(dauphin.String)),
    )

    schedules = dauphin.non_null_list('ScheduleDefinition')

    scheduler = dauphin.Field(dauphin.NonNull('SchedulerOrError'))

    pipelineRuns = dauphin.non_null_list('PipelineRun')

    pipelineRunOrError = dauphin.Field(
        dauphin.NonNull('PipelineRunOrError'), runId=dauphin.NonNull(dauphin.ID)
    )

    isPipelineConfigValid = dauphin.Field(
        dauphin.NonNull('PipelineConfigValidationResult'),
        args={
            'pipeline': dauphin.Argument(dauphin.NonNull('ExecutionSelector')),
            'environmentConfigData': dauphin.Argument('EnvironmentConfigData'),
            'mode': dauphin.Argument(dauphin.NonNull(dauphin.String)),
        },
    )

    executionPlan = dauphin.Field(
        dauphin.NonNull('ExecutionPlanResult'),
        args={
            'pipeline': dauphin.Argument(dauphin.NonNull('ExecutionSelector')),
            'environmentConfigData': dauphin.Argument('EnvironmentConfigData'),
            'mode': dauphin.Argument(dauphin.NonNull(dauphin.String)),
        },
    )

    environmentSchemaOrError = dauphin.Field(
        dauphin.NonNull('EnvironmentSchemaOrError'),
        args={
            'selector': dauphin.Argument(dauphin.NonNull('ExecutionSelector')),
            'mode': dauphin.Argument(dauphin.NonNull(dauphin.String)),
        },
        description='''Fetch an environment schema given an execution selection and a mode.
        See the descripton on EnvironmentSchema for more information.''',
    )

    enabledFeatures = dauphin.non_null_list(dauphin.String)

    def resolve_configTypeOrError(self, graphene_info, **kwargs):
        return get_config_type(
            graphene_info, kwargs['pipelineName'], kwargs['configTypeName'], kwargs.get('mode')
        )

    def resolve_runtimeTypeOrError(self, graphene_info, **kwargs):
        return get_runtime_type(graphene_info, kwargs['pipelineName'], kwargs['runtimeTypeName'])

    def resolve_version(self, graphene_info):
        return graphene_info.context.version

    def resolve_schedules(self, graphene_info):
        return get_schedules(graphene_info)

    def resolve_scheduler(self, graphene_info):
        return get_scheduler_or_error(graphene_info)

    def resolve_pipelineOrError(self, graphene_info, **kwargs):
        return get_pipeline_or_error(graphene_info, kwargs['params'].to_selector())

    def resolve_pipeline(self, graphene_info, **kwargs):
        return get_pipeline_or_raise(graphene_info, kwargs['params'].to_selector())

    def resolve_pipelinesOrError(self, graphene_info):
        return get_pipelines_or_error(graphene_info)

    def resolve_pipelines(self, graphene_info):
        return get_pipelines_or_raise(graphene_info)

    def resolve_pipelineRuns(self, graphene_info):
        return get_runs(graphene_info)

    def resolve_pipelineRunOrError(self, graphene_info, runId):
        return get_run(graphene_info, runId)

    def resolve_isPipelineConfigValid(self, graphene_info, pipeline, **kwargs):
        return validate_pipeline_config(
            graphene_info,
            pipeline.to_selector(),
            kwargs.get('environmentConfigData'),
            kwargs.get('mode'),
        )

    def resolve_executionPlan(self, graphene_info, pipeline, **kwargs):
        return get_execution_plan(
            graphene_info,
            pipeline.to_selector(),
            kwargs.get('environmentConfigData'),
            kwargs.get('mode'),
        )

    def resolve_environmentSchemaOrError(self, graphene_info, **kwargs):
        return resolve_environment_schema_or_error(
            graphene_info, kwargs['selector'].to_selector(), kwargs['mode']
        )

    def resolve_enabledFeatures(self, graphene_info):
        return [
            entry.name
            for entry in DagsterFeatures
            if graphene_info.context.instance.is_feature_enabled(entry)
        ]


class DauphinStepOutputHandle(dauphin.InputObjectType):
    class Meta:
        name = 'StepOutputHandle'

    stepKey = dauphin.NonNull(dauphin.String)
    outputName = dauphin.NonNull(dauphin.String)


class DauphinReexecutionConfig(dauphin.InputObjectType):
    class Meta:
        name = 'ReexecutionConfig'

    previousRunId = dauphin.NonNull(dauphin.String)
    stepOutputHandles = dauphin.non_null_list(DauphinStepOutputHandle)

    def to_reexecution_config(self):
        from dagster.core.execution.config import ReexecutionConfig
        from dagster.core.execution.plan.objects import StepOutputHandle

        return ReexecutionConfig(
            self.previousRunId,
            list(map(lambda g: StepOutputHandle(g.stepKey, g.outputName), self.stepOutputHandles)),
        )


class DauphinStartPipelineExecutionMutation(dauphin.Mutation):
    class Meta:
        name = 'StartPipelineExecutionMutation'

    class Arguments:
        executionParams = dauphin.NonNull('ExecutionParams')
        reexecutionConfig = dauphin.Argument('ReexecutionConfig')

    Output = dauphin.NonNull('StartPipelineExecutionResult')

    def mutate(self, graphene_info, **kwargs):
        return start_pipeline_execution(
            graphene_info,
            execution_params=create_execution_params(graphene_info, kwargs['executionParams']),
            reexecution_config=kwargs['reexecutionConfig'].to_reexecution_config()
            if 'reexecutionConfig' in kwargs
            else None,
        )


class DauphinExecutionTag(dauphin.InputObjectType):
    class Meta:
        name = 'ExecutionTag'

    key = dauphin.NonNull(dauphin.String)
    value = dauphin.NonNull(dauphin.String)


class DauphinMarshalledInput(dauphin.InputObjectType):
    class Meta:
        name = 'MarshalledInput'

    input_name = dauphin.NonNull(dauphin.String)
    key = dauphin.NonNull(dauphin.String)


class DauphinMarshalledOutput(dauphin.InputObjectType):
    class Meta:
        name = 'MarshalledOutput'

    output_name = dauphin.NonNull(dauphin.String)
    key = dauphin.NonNull(dauphin.String)


class DauphinStepExecution(dauphin.InputObjectType):
    class Meta:
        name = 'StepExecution'

    stepKey = dauphin.NonNull(dauphin.String)
    marshalledInputs = dauphin.List(dauphin.NonNull(DauphinMarshalledInput))
    marshalledOutputs = dauphin.List(dauphin.NonNull(DauphinMarshalledOutput))


class DauphinExecutionMetadata(dauphin.InputObjectType):
    class Meta:
        name = 'ExecutionMetadata'

    runId = dauphin.String()
    tags = dauphin.List(dauphin.NonNull(DauphinExecutionTag))


def create_execution_params(graphene_info, graphql_execution_params):

    preset_name = graphql_execution_params.get('preset')
    if preset_name:
        check.invariant(
            not graphql_execution_params.get('environmentConfigData'),
            "Invalid ExecutionParams. Cannot define environment_dict when using preset",
        )
        check.invariant(
            not graphql_execution_params.get('mode'),
            "Invalid ExecutionParams. Cannot define mode when using preset",
        )

        selector = graphql_execution_params['selector'].to_selector()
        check.invariant(
            not selector.solid_subset,
            "Invalid ExecutionParams. Cannot define selector.solid_subset when using preset",
        )
        dauphin_pipeline = get_dauphin_pipeline_from_selector(graphene_info, selector)
        pipeline = dauphin_pipeline.get_dagster_pipeline()

        if not pipeline.has_preset(preset_name):
            raise UserFacingGraphQLError(
                graphene_info.schema.type_named('PresetNotFoundError')(
                    preset=preset_name, selector=selector
                )
            )

        preset = pipeline.get_preset(preset_name)

        return ExecutionParams(
            selector=ExecutionSelector(selector.name, preset.solid_subset),
            environment_dict=preset.environment_dict,
            mode=preset.mode,
            execution_metadata=ExecutionMetadata(run_id=None, tags={}),
            step_keys=graphql_execution_params.get('stepKeys'),
        )

    return ExecutionParams(
        selector=graphql_execution_params['selector'].to_selector(),
        environment_dict=graphql_execution_params.get('environmentConfigData'),
        mode=graphql_execution_params.get('mode'),
        execution_metadata=create_execution_metadata(
            graphql_execution_params.get('executionMetadata')
        ),
        step_keys=graphql_execution_params.get('stepKeys'),
    )


def create_execution_metadata(graphql_execution_metadata):
    return (
        ExecutionMetadata(
            graphql_execution_metadata.get('runId'),
            {t['key']: t['value'] for t in graphql_execution_metadata.get('tags', [])},
        )
        if graphql_execution_metadata
        else ExecutionMetadata(run_id=None, tags={})
    )


class DauphinExecutePlan(dauphin.Mutation):
    class Meta:
        name = 'ExecutePlan'

    class Arguments:
        executionParams = dauphin.NonNull('ExecutionParams')

    Output = dauphin.NonNull('ExecutePlanResult')

    def mutate(self, graphene_info, **kwargs):
        return do_execute_plan(
            graphene_info, create_execution_params(graphene_info, kwargs['executionParams'])
        )


class DauphinMutation(dauphin.ObjectType):
    class Meta:
        name = 'Mutation'

    start_pipeline_execution = DauphinStartPipelineExecutionMutation.Field()
    execute_plan = DauphinExecutePlan.Field()
    start_schedule = DauphinStartScheduleMutation.Field()
    end_running_schedule = DauphinEndRunningScheduleMutation.Field()


class DauphinSubscription(dauphin.ObjectType):
    class Meta:
        name = 'Subscription'

    pipelineRunLogs = dauphin.Field(
        dauphin.NonNull('PipelineRunLogsSubscriptionPayload'),
        runId=dauphin.Argument(dauphin.NonNull(dauphin.ID)),
        after=dauphin.Argument('Cursor'),
    )

    computeLogs = dauphin.Field(
        dauphin.NonNull('ComputeLogs'),
        runId=dauphin.Argument(dauphin.NonNull(dauphin.ID)),
        stepKey=dauphin.Argument(dauphin.NonNull(dauphin.String)),
        cursor=dauphin.Argument('Cursor'),
    )

    def resolve_pipelineRunLogs(self, graphene_info, runId, after=None):
        return get_pipeline_run_observable(graphene_info, runId, after)

    def resolve_computeLogs(self, graphene_info, runId, stepKey, cursor=None):
        return get_compute_log_observable(graphene_info, runId, stepKey, cursor)


class DauphinEnvironmentConfigData(dauphin.GenericScalar, dauphin.Scalar):
    class Meta:
        name = 'EnvironmentConfigData'
        description = '''This type is used when passing in a configuration object
        for pipeline configuration. This is any-typed in the GraphQL type system,
        but must conform to the constraints of the dagster config type system'''


class DauphinExecutionParams(dauphin.InputObjectType):
    class Meta:
        name = 'ExecutionParams'

    selector = dauphin.NonNull('ExecutionSelector')
    environmentConfigData = dauphin.Field('EnvironmentConfigData')
    mode = dauphin.Field(dauphin.String)
    executionMetadata = dauphin.Field('ExecutionMetadata')
    stepKeys = dauphin.Field(dauphin.List(dauphin.NonNull(dauphin.String)))
    preset = dauphin.Field(dauphin.String)


class DauphinExecutionSelector(dauphin.InputObjectType):
    class Meta:
        name = 'ExecutionSelector'
        description = '''This type represents the fields necessary to identify a
        pipeline or pipeline subset.'''

    name = dauphin.NonNull(dauphin.String)
    solidSubset = dauphin.List(dauphin.NonNull(dauphin.String))

    def to_selector(self):
        return ExecutionSelector(self.name, self.solidSubset)


class DauphinEnvironmentSchema(dauphin.ObjectType):
    def __init__(self, environment_schema, dagster_pipeline):
        from dagster.core.definitions.environment_schema import EnvironmentSchema
        from dagster.core.definitions.pipeline import PipelineDefinition

        self._environment_schema = check.inst_param(
            environment_schema, 'environment_schema', EnvironmentSchema
        )

        self._dagster_pipeline = check.inst_param(
            dagster_pipeline, 'dagster_pipeline', PipelineDefinition
        )

    class Meta:
        name = 'EnvironmentSchema'
        description = '''The environment schema represents the all the config type
        information given a certain execution selection and mode of execution of that
        selection. All config interactions (e.g. checking config validity, fetching
        all config types, fetching in a particular config type) should be done
        through this type '''

    rootEnvironmentType = dauphin.Field(
        dauphin.NonNull('ConfigType'),
        description='''Fetch the root environment type. Concretely this is the type that
        is in scope at the root of configuration document for a particular execution selection.
        It is the type that is in scope initially with a blank config editor.''',
    )
    allConfigTypes = dauphin.Field(
        dauphin.non_null_list('ConfigType'),
        description='''Fetch all the named config types that are in the schema. Useful
        for things like a type browser UI, or for fetching all the types are in the
        scope of a document so that the index can be built for the autocompleting editor.
    ''',
    )
    configTypeOrError = dauphin.Field(
        dauphin.NonNull('ConfigTypeOrError'),
        configTypeName=dauphin.Argument(dauphin.NonNull(dauphin.String)),
        description='''Fetch a particular config type''',
    )

    isEnvironmentConfigValid = dauphin.Field(
        dauphin.NonNull('PipelineConfigValidationResult'),
        args={'environmentConfigData': dauphin.Argument('EnvironmentConfigData')},
        description='''Parse a particular environment config result. The return value
        either indicates that the validation succeeded by returning
        `PipelineConfigValidationValid` or that there are configuration errors
        by returning `PipelineConfigValidationInvalid' which containers a list errors
        so that can be rendered for the user''',
    )

    def resolve_allConfigTypes(self, _graphene_info):
        return sorted(
            list(map(to_dauphin_config_type, self._environment_schema.all_config_types())),
            key=lambda ct: ct.name if ct.name else '',
        )

    def resolve_rootEnvironmentType(self, _graphene_info):
        return to_dauphin_config_type(self._environment_schema.environment_type)

    def resolve_configTypeOrError(self, graphene_info, **kwargs):
        return resolve_config_type_or_error(
            graphene_info,
            self._environment_schema,
            self._dagster_pipeline,
            kwargs['configTypeName'],
        )

    def resolve_isEnvironmentConfigValid(self, graphene_info, **kwargs):
        return resolve_is_environment_config_valid(
            graphene_info,
            self._environment_schema,
            self._dagster_pipeline,
            kwargs.get('environmentConfigData'),
        )


class DauphinEnvironmentSchemaOrError(dauphin.Union):
    class Meta:
        name = 'EnvironmentSchemaOrError'
        types = (
            'EnvironmentSchema',
            'PipelineNotFoundError',
            'InvalidSubsetError',
            'ModeNotFoundError',
        )
