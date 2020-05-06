# commment
from dagster_graphql import dauphin
from dagster_graphql.implementation.environment_schema import (
    resolve_environment_schema_or_error,
    resolve_is_environment_config_valid,
)
from dagster_graphql.implementation.execution import (
    ExecutionParams,
    cancel_pipeline_execution,
    delete_pipeline_run,
    do_execute_plan,
    get_compute_log_observable,
    get_pipeline_run_observable,
    launch_pipeline_execution,
    launch_pipeline_reexecution,
    start_pipeline_execution,
    start_pipeline_reexecution,
    start_scheduled_execution,
)
from dagster_graphql.implementation.execution.start_execution import (
    start_pipeline_execution_for_created_run,
)
from dagster_graphql.implementation.external import get_external_pipeline_or_raise
from dagster_graphql.implementation.fetch_assets import get_asset, get_assets
from dagster_graphql.implementation.fetch_partition_sets import (
    get_partition_set,
    get_partition_sets_or_error,
)
from dagster_graphql.implementation.fetch_pipelines import (
    get_pipeline_or_error,
    get_pipeline_or_raise,
    get_pipeline_snapshot,
    get_pipeline_snapshot_or_error_from_pipeline_name,
    get_pipeline_snapshot_or_error_from_snapshot_id,
    get_pipelines_or_error,
    get_pipelines_or_raise,
)
from dagster_graphql.implementation.fetch_runs import (
    get_execution_plan,
    get_run_by_id,
    get_run_group,
    get_run_tags,
    get_runs,
    validate_pipeline_config,
)
from dagster_graphql.implementation.fetch_schedules import (
    get_schedule_or_error,
    get_scheduler_or_error,
)
from dagster_graphql.implementation.fetch_solids import get_solid, get_solids
from dagster_graphql.implementation.utils import ExecutionMetadata, UserFacingGraphQLError

from dagster import check
from dagster.core.definitions.pipeline import ExecutionSelector
from dagster.core.instance import DagsterInstance
from dagster.core.launcher import RunLauncher
from dagster.core.snap import PipelineIndex
from dagster.core.storage.compute_log_manager import ComputeIOType
from dagster.core.storage.pipeline_run import PipelineRunStatus, PipelineRunsFilter

from .config_types import to_dauphin_config_type
from .runs import DauphinPipelineRunStatus
from .schedules import DauphinStartScheduleMutation, DauphinStopRunningScheduleMutation


class DauphinQuery(dauphin.ObjectType):
    class Meta(object):
        name = 'Query'

    version = dauphin.NonNull(dauphin.String)
    reloadSupported = dauphin.NonNull(dauphin.Boolean)

    pipelineOrError = dauphin.Field(
        dauphin.NonNull('PipelineOrError'), params=dauphin.NonNull('ExecutionSelector')
    )
    pipeline = dauphin.Field(
        dauphin.NonNull('Pipeline'), params=dauphin.NonNull('ExecutionSelector')
    )
    pipelinesOrError = dauphin.NonNull('PipelinesOrError')
    pipelines = dauphin.Field(dauphin.NonNull('PipelineConnection'))

    pipelineSnapshot = dauphin.Field(
        dauphin.NonNull('PipelineSnapshot'),
        snapshotId=dauphin.Argument(dauphin.NonNull(dauphin.String)),
    )

    pipelineSnapshotOrError = dauphin.Field(
        dauphin.NonNull('PipelineSnapshotOrError'),
        snapshotId=dauphin.String(),
        activePipelineName=dauphin.String(),
    )

    scheduler = dauphin.Field(dauphin.NonNull('SchedulerOrError'))
    scheduleOrError = dauphin.Field(
        dauphin.NonNull('ScheduleOrError'),
        schedule_name=dauphin.NonNull(dauphin.String),
        limit=dauphin.Int(),
    )

    partitionSetsOrError = dauphin.Field(
        dauphin.NonNull('PartitionSetsOrError'), pipelineName=dauphin.String()
    )
    partitionSetOrError = dauphin.Field(
        dauphin.NonNull('PartitionSetOrError'), partitionSetName=dauphin.String()
    )

    pipelineRunsOrError = dauphin.Field(
        dauphin.NonNull('PipelineRunsOrError'),
        filter=dauphin.Argument('PipelineRunsFilter'),
        cursor=dauphin.String(),
        limit=dauphin.Int(),
    )

    pipelineRunOrError = dauphin.Field(
        dauphin.NonNull('PipelineRunOrError'), runId=dauphin.NonNull(dauphin.ID)
    )

    pipelineRunTags = dauphin.non_null_list('PipelineTagAndValues')

    runGroupOrError = dauphin.Field(
        dauphin.NonNull('RunGroupOrError'), runId=dauphin.NonNull(dauphin.ID)
    )

    usedSolids = dauphin.Field(dauphin.non_null_list('UsedSolid'))
    usedSolid = dauphin.Field('UsedSolid', name=dauphin.NonNull(dauphin.String))

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
            'mode': dauphin.Argument(dauphin.String),
        },
        description='''Fetch an environment schema given an execution selection and a mode.
        See the descripton on EnvironmentSchema for more information.''',
    )

    instance = dauphin.NonNull('Instance')
    assetsOrError = dauphin.Field(dauphin.NonNull('AssetsOrError'))
    assetOrError = dauphin.Field(
        dauphin.NonNull('AssetOrError'), assetKey=dauphin.NonNull(dauphin.String)
    )

    def resolve_pipelineSnapshot(self, graphene_info, **kwargs):
        return get_pipeline_snapshot(graphene_info, kwargs['snapshotId'])

    def resolve_pipelineSnapshotOrError(self, graphene_info, **kwargs):
        snapshot_id_arg = kwargs.get('snapshotId')
        pipeline_name_arg = kwargs.get('activePipelineName')
        check.invariant(
            not (snapshot_id_arg and pipeline_name_arg),
            'Cannot pass both snapshotId and activePipelineName',
        )
        check.invariant(
            snapshot_id_arg or pipeline_name_arg, 'Must set one of snapshotId or activePipelineName'
        )

        if pipeline_name_arg:
            return get_pipeline_snapshot_or_error_from_pipeline_name(
                graphene_info, pipeline_name_arg
            )
        else:
            return get_pipeline_snapshot_or_error_from_snapshot_id(graphene_info, snapshot_id_arg)

    def resolve_version(self, graphene_info):
        return graphene_info.context.version

    def resolve_reloadSupported(self, graphene_info):
        return graphene_info.context.is_reload_supported

    def resolve_scheduler(self, graphene_info):
        return get_scheduler_or_error(graphene_info)

    def resolve_scheduleOrError(self, graphene_info, schedule_name):
        return get_schedule_or_error(graphene_info, schedule_name)

    def resolve_pipelineOrError(self, graphene_info, **kwargs):
        return get_pipeline_or_error(graphene_info, kwargs['params'].to_selector())

    def resolve_pipeline(self, graphene_info, **kwargs):
        return get_pipeline_or_raise(graphene_info, kwargs['params'].to_selector())

    def resolve_pipelinesOrError(self, graphene_info):
        return get_pipelines_or_error(graphene_info)

    def resolve_pipelines(self, graphene_info):
        return get_pipelines_or_raise(graphene_info)

    def resolve_pipelineRunsOrError(self, graphene_info, **kwargs):
        filters = kwargs.get('filter')
        if filters is not None:
            filters = filters.to_selector()

        return graphene_info.schema.type_named('PipelineRuns')(
            results=get_runs(graphene_info, filters, kwargs.get('cursor'), kwargs.get('limit'))
        )

    def resolve_pipelineRunOrError(self, graphene_info, runId):
        return get_run_by_id(graphene_info, runId)

    def resolve_partitionSetsOrError(self, graphene_info, **kwargs):
        pipeline_name = kwargs.get('pipelineName')

        return get_partition_sets_or_error(graphene_info, pipeline_name)

    def resolve_partitionSetOrError(self, graphene_info, partitionSetName):
        return get_partition_set(graphene_info, partitionSetName)

    def resolve_pipelineRunTags(self, graphene_info):
        return get_run_tags(graphene_info)

    def resolve_runGroupOrError(self, graphene_info, runId):
        return get_run_group(graphene_info, runId)

    def resolve_usedSolid(self, graphene_info, name):
        return get_solid(graphene_info, name)

    def resolve_usedSolids(self, graphene_info):
        return get_solids(graphene_info)

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
            graphene_info, kwargs['selector'].to_selector(), kwargs.get('mode')
        )

    def resolve_instance(self, graphene_info):
        return graphene_info.schema.type_named('Instance')(graphene_info.context.instance)

    def resolve_assetsOrError(self, graphene_info):
        return get_assets(graphene_info)

    def resolve_assetOrError(self, graphene_info, assetKey):
        return get_asset(graphene_info, assetKey)


class DauphinStepOutputHandle(dauphin.InputObjectType):
    class Meta(object):
        name = 'StepOutputHandle'

    stepKey = dauphin.NonNull(dauphin.String)
    outputName = dauphin.NonNull(dauphin.String)


class DauphinDeletePipelineRunSuccess(dauphin.ObjectType):
    class Meta(object):
        name = 'DeletePipelineRunSuccess'

    runId = dauphin.NonNull(dauphin.String)


class DauphinDeletePipelineRunResult(dauphin.Union):
    class Meta(object):
        name = 'DeletePipelineRunResult'
        types = ('DeletePipelineRunSuccess', 'PythonError', 'PipelineRunNotFoundError')


class DauphinDeleteRunMutation(dauphin.Mutation):
    class Meta(object):
        name = 'DeletePipelineRun'

    class Arguments(object):
        runId = dauphin.NonNull(dauphin.String)

    Output = dauphin.NonNull('DeletePipelineRunResult')

    def mutate(self, graphene_info, **kwargs):
        run_id = kwargs['runId']
        return delete_pipeline_run(graphene_info, run_id)


class DauphinCancelPipelineExecutionSuccess(dauphin.ObjectType):
    class Meta(object):
        name = 'CancelPipelineExecutionSuccess'

    run = dauphin.Field(dauphin.NonNull('PipelineRun'))


class DauphinCancelPipelineExecutionFailure(dauphin.ObjectType):
    class Meta(object):
        name = 'CancelPipelineExecutionFailure'

    run = dauphin.NonNull('PipelineRun')
    message = dauphin.NonNull(dauphin.String)


class DauphinCancelPipelineExecutionResult(dauphin.Union):
    class Meta(object):
        name = 'CancelPipelineExecutionResult'
        types = (
            'CancelPipelineExecutionSuccess',
            'CancelPipelineExecutionFailure',
            'PipelineRunNotFoundError',
            'PythonError',
        )


class DauphinStartScheduledExecutionMutation(dauphin.Mutation):
    class Meta(object):
        name = 'StartScheduledExecutionMutation'

    class Arguments(object):
        scheduleName = dauphin.NonNull(dauphin.String)

    Output = dauphin.NonNull('StartScheduledExecutionResult')

    def mutate(self, graphene_info, scheduleName):
        return start_scheduled_execution(graphene_info, schedule_name=scheduleName)


class DauphinStartPipelineExecutionMutation(dauphin.Mutation):
    class Meta(object):
        name = 'StartPipelineExecutionMutation'
        description = (
            'Execute a pipeline run in the python environment '
            'dagit/dagster-graphql is currently operating in.'
        )

    class Arguments(object):
        executionParams = dauphin.NonNull('ExecutionParams')

    Output = dauphin.NonNull('StartPipelineExecutionResult')

    def mutate(self, graphene_info, **kwargs):
        return start_pipeline_execution(
            graphene_info,
            execution_params=create_execution_params(graphene_info, kwargs['executionParams']),
        )


class DauphinStartPipelineExecutionForCreatedRunMutation(dauphin.Mutation):
    class Meta(object):
        name = 'StartPipelineExecutionForCreatedRunMutation'
        description = (
            'Execute a pipeline run in the python environment '
            'dagit/dagster-graphql is currently operating in.'
        )

    class Arguments(object):
        run_id = dauphin.NonNull(dauphin.String)

    Output = dauphin.NonNull('StartPipelineExecutionForCreatedRunResult')

    def mutate(self, graphene_info, run_id):
        return start_pipeline_execution_for_created_run(graphene_info, run_id=run_id)


class DauphinLaunchPipelineExecutionMutation(dauphin.Mutation):
    class Meta(object):
        name = 'LaunchPipelineExecutionMutation'
        description = 'Launch a pipeline run via the run launcher configured on the instance.'

    class Arguments(object):
        executionParams = dauphin.NonNull('ExecutionParams')

    Output = dauphin.NonNull('LaunchPipelineExecutionResult')

    def mutate(self, graphene_info, **kwargs):
        return launch_pipeline_execution(
            graphene_info,
            execution_params=create_execution_params(graphene_info, kwargs['executionParams']),
        )


class DauphinStartPipelineReexecutionMutation(dauphin.Mutation):
    class Meta(object):
        name = 'DauphinStartPipelineReexecutionMutation'
        description = (
            'Re-execute a pipeline run in the python environment '
            'dagit/dagster-graphql is currently operating in.'
        )

    class Arguments(object):
        executionParams = dauphin.NonNull('ExecutionParams')

    Output = dauphin.NonNull('StartPipelineReexecutionResult')

    def mutate(self, graphene_info, **kwargs):
        return start_pipeline_reexecution(
            graphene_info,
            execution_params=create_execution_params(graphene_info, kwargs['executionParams']),
        )


class DauphinLaunchPipelineReexecutionMutation(dauphin.Mutation):
    class Meta(object):
        name = 'DauphinLaunchPipelineReexecutionMutation'
        description = 'Re-launch a pipeline run via the run launcher configured on the instance'

    class Arguments(object):
        executionParams = dauphin.NonNull('ExecutionParams')

    Output = dauphin.NonNull('LaunchPipelineReexecutionResult')

    def mutate(self, graphene_info, **kwargs):
        return launch_pipeline_reexecution(
            graphene_info,
            execution_params=create_execution_params(graphene_info, kwargs['executionParams']),
        )


class DauphinCancelPipelineExecutionMutation(dauphin.Mutation):
    class Meta(object):
        name = 'CancelPipelineExecutionMutation'

    class Arguments(object):
        runId = dauphin.NonNull(dauphin.String)

    Output = dauphin.NonNull('CancelPipelineExecutionResult')

    def mutate(self, graphene_info, **kwargs):
        return cancel_pipeline_execution(graphene_info, kwargs['runId'])


class DauphinExecutionTag(dauphin.InputObjectType):
    class Meta(object):
        name = 'ExecutionTag'

    key = dauphin.NonNull(dauphin.String)
    value = dauphin.NonNull(dauphin.String)


class DauphinMarshalledInput(dauphin.InputObjectType):
    class Meta(object):
        name = 'MarshalledInput'

    input_name = dauphin.NonNull(dauphin.String)
    key = dauphin.NonNull(dauphin.String)


class DauphinMarshalledOutput(dauphin.InputObjectType):
    class Meta(object):
        name = 'MarshalledOutput'

    output_name = dauphin.NonNull(dauphin.String)
    key = dauphin.NonNull(dauphin.String)


class DauphinStepExecution(dauphin.InputObjectType):
    class Meta(object):
        name = 'StepExecution'

    stepKey = dauphin.NonNull(dauphin.String)
    marshalledInputs = dauphin.List(dauphin.NonNull(DauphinMarshalledInput))
    marshalledOutputs = dauphin.List(dauphin.NonNull(DauphinMarshalledOutput))


class DauphinExecutionMetadata(dauphin.InputObjectType):
    class Meta(object):
        name = 'ExecutionMetadata'

    runId = dauphin.String()
    tags = dauphin.List(dauphin.NonNull(DauphinExecutionTag))
    rootRunId = dauphin.String()
    parentRunId = dauphin.String()


def create_execution_params(graphene_info, graphql_execution_params):

    preset_name = graphql_execution_params.get('preset')
    if preset_name:
        check.invariant(
            not graphql_execution_params.get('environmentConfigData'),
            'Invalid ExecutionParams. Cannot define environment_dict when using preset',
        )
        check.invariant(
            not graphql_execution_params.get('mode'),
            'Invalid ExecutionParams. Cannot define mode when using preset',
        )

        selector = graphql_execution_params['selector'].to_selector()
        check.invariant(
            not selector.solid_subset,
            'Invalid ExecutionParams. Cannot define selector.solid_subset when using preset',
        )

        external_pipeline = get_external_pipeline_or_raise(graphene_info, selector.name)

        if not external_pipeline.has_preset(preset_name):
            raise UserFacingGraphQLError(
                graphene_info.schema.type_named('PresetNotFoundError')(
                    preset=preset_name, selector=selector
                )
            )

        preset = external_pipeline.get_preset(preset_name)

        return ExecutionParams(
            selector=ExecutionSelector(selector.name, preset.solid_subset),
            environment_dict=preset.environment_dict,
            mode=preset.mode,
            execution_metadata=create_execution_metadata(
                graphql_execution_params.get('executionMetadata')
            ),
            step_keys=graphql_execution_params.get('stepKeys'),
        )

    return execution_params_from_graphql(graphql_execution_params)


def execution_params_from_graphql(graphql_execution_params):
    return ExecutionParams(
        selector=ExecutionSelector.from_dict(graphql_execution_params.get('selector')),
        environment_dict=graphql_execution_params.get('environmentConfigData') or {},
        mode=graphql_execution_params.get('mode'),
        execution_metadata=create_execution_metadata(
            graphql_execution_params.get('executionMetadata')
        ),
        step_keys=graphql_execution_params.get('stepKeys'),
    )


def create_execution_metadata(graphql_execution_metadata):
    return (
        ExecutionMetadata(
            run_id=graphql_execution_metadata.get('runId'),
            tags={t['key']: t['value'] for t in graphql_execution_metadata.get('tags', [])},
            root_run_id=graphql_execution_metadata.get('rootRunId'),
            parent_run_id=graphql_execution_metadata.get('parentRunId'),
        )
        if graphql_execution_metadata
        else ExecutionMetadata(run_id=None, tags={})
    )


class DauphinExecutePlan(dauphin.Mutation):
    class Meta(object):
        name = 'ExecutePlan'

    class Arguments(object):
        executionParams = dauphin.NonNull('ExecutionParams')

    Output = dauphin.NonNull('ExecutePlanResult')

    def mutate(self, graphene_info, **kwargs):
        return do_execute_plan(
            graphene_info, create_execution_params(graphene_info, kwargs['executionParams'])
        )


class DauphinReloadDagit(dauphin.Mutation):
    class Meta(object):
        name = 'ReloadDagit'

    Output = dauphin.NonNull(dauphin.Boolean)

    def mutate(self, graphene_info):
        return graphene_info.context.reloader.reload()


class DauphinMutation(dauphin.ObjectType):
    class Meta(object):
        name = 'Mutation'

    start_pipeline_execution = DauphinStartPipelineExecutionMutation.Field()
    start_pipeline_execution_for_created_run = (
        DauphinStartPipelineExecutionForCreatedRunMutation.Field()
    )
    start_scheduled_execution = DauphinStartScheduledExecutionMutation.Field()
    launch_pipeline_execution = DauphinLaunchPipelineExecutionMutation.Field()
    start_pipeline_reexecution = DauphinStartPipelineReexecutionMutation.Field()
    launch_pipeline_reexecution = DauphinLaunchPipelineReexecutionMutation.Field()
    execute_plan = DauphinExecutePlan.Field()
    start_schedule = DauphinStartScheduleMutation.Field()
    stop_running_schedule = DauphinStopRunningScheduleMutation.Field()
    reload_dagit = DauphinReloadDagit.Field()
    cancel_pipeline_execution = DauphinCancelPipelineExecutionMutation.Field()
    delete_pipeline_run = DauphinDeleteRunMutation.Field()


DauphinComputeIOType = dauphin.Enum.from_enum(ComputeIOType)


class DauphinSubscription(dauphin.ObjectType):
    class Meta(object):
        name = 'Subscription'

    pipelineRunLogs = dauphin.Field(
        dauphin.NonNull('PipelineRunLogsSubscriptionPayload'),
        runId=dauphin.Argument(dauphin.NonNull(dauphin.ID)),
        after=dauphin.Argument('Cursor'),
    )

    computeLogs = dauphin.Field(
        dauphin.NonNull('ComputeLogFile'),
        runId=dauphin.Argument(dauphin.NonNull(dauphin.ID)),
        stepKey=dauphin.Argument(dauphin.NonNull(dauphin.String)),
        ioType=dauphin.Argument(dauphin.NonNull('ComputeIOType')),
        cursor=dauphin.Argument(dauphin.String),
    )

    def resolve_pipelineRunLogs(self, graphene_info, runId, after=None):
        return get_pipeline_run_observable(graphene_info, runId, after)

    def resolve_computeLogs(self, graphene_info, runId, stepKey, ioType, cursor=None):
        check.str_param(ioType, 'ioType')  # need to resolve to enum
        return get_compute_log_observable(
            graphene_info, runId, stepKey, ComputeIOType(ioType), cursor
        )


class DauphinEnvironmentConfigData(dauphin.GenericScalar, dauphin.Scalar):
    class Meta(object):
        name = 'EnvironmentConfigData'
        description = '''This type is used when passing in a configuration object
        for pipeline configuration. This is any-typed in the GraphQL type system,
        but must conform to the constraints of the dagster config type system'''


class DauphinExecutionParams(dauphin.InputObjectType):
    class Meta(object):
        name = 'ExecutionParams'

    selector = dauphin.NonNull('ExecutionSelector')
    environmentConfigData = dauphin.Field('EnvironmentConfigData')
    mode = dauphin.Field(dauphin.String)
    executionMetadata = dauphin.Field('ExecutionMetadata')
    stepKeys = dauphin.Field(dauphin.List(dauphin.NonNull(dauphin.String)))
    preset = dauphin.Field(dauphin.String)


class DauphinExecutionSelector(dauphin.InputObjectType):
    class Meta(object):
        name = 'ExecutionSelector'
        description = '''This type represents the fields necessary to identify a
        pipeline or pipeline subset.'''

    name = dauphin.NonNull(dauphin.String)
    solidSubset = dauphin.List(dauphin.NonNull(dauphin.String))

    def to_selector(self):
        return ExecutionSelector(self.name, self.solidSubset)


class DauphinPipelineRunsFilter(dauphin.InputObjectType):
    class Meta(object):
        name = 'PipelineRunsFilter'
        description = '''This type represents a filter on pipeline runs.
        Currently, you may only pass one of the filter options.'''

    # Currently you may choose one of the following
    run_id = dauphin.Field(dauphin.String)
    pipeline_name = dauphin.Field(dauphin.String)
    tags = dauphin.List(dauphin.NonNull(DauphinExecutionTag))
    status = dauphin.Field(DauphinPipelineRunStatus)

    def to_selector(self):
        if self.status:
            status = PipelineRunStatus[self.status]
        else:
            status = None

        if self.tags:
            # We are wrapping self.tags in a list because dauphin.List is not marked as iterable
            tags = {tag['key']: tag['value'] for tag in list(self.tags)}
        else:
            tags = None

        run_ids = [self.run_id] if self.run_id else []
        return PipelineRunsFilter(
            run_ids=run_ids, pipeline_name=self.pipeline_name, tags=tags, status=status,
        )


class DauphinPipelineTagAndValues(dauphin.ObjectType):
    class Meta(object):
        name = 'PipelineTagAndValues'
        description = '''A run tag and the free-form values that have been associated
        with it so far.'''

    key = dauphin.NonNull(dauphin.String)
    values = dauphin.non_null_list(dauphin.String)


class DauphinEnvironmentSchema(dauphin.ObjectType):
    def __init__(self, pipeline_index, mode):
        self._pipeline_index = check.inst_param(pipeline_index, 'pipeline_index', PipelineIndex)
        self._mode = check.str_param(mode, 'mode')

    class Meta(object):
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
            list(
                map(
                    lambda key: to_dauphin_config_type(
                        self._pipeline_index.config_schema_snapshot, key
                    ),
                    self._pipeline_index.config_schema_snapshot.all_config_keys,
                )
            ),
            key=lambda ct: ct.key,
        )

    def resolve_rootEnvironmentType(self, _graphene_info):
        return to_dauphin_config_type(
            self._pipeline_index.config_schema_snapshot,
            self._pipeline_index.get_mode_def_snap(self._mode).root_config_key,
        )

    def resolve_isEnvironmentConfigValid(self, graphene_info, **kwargs):
        return resolve_is_environment_config_valid(
            graphene_info,
            self._pipeline_index,
            self._mode,
            kwargs.get('environmentConfigData', {}),
        )


class DauphinEnvironmentSchemaOrError(dauphin.Union):
    class Meta(object):
        name = 'EnvironmentSchemaOrError'
        types = (
            'EnvironmentSchema',
            'PipelineNotFoundError',
            'InvalidSubsetError',
            'ModeNotFoundError',
            'PythonError',
        )


class DauhphinRunLauncher(dauphin.ObjectType):
    class Meta(object):
        name = 'RunLauncher'

    name = dauphin.NonNull(dauphin.String)

    def __init__(self, run_launcher):
        self._run_launcher = check.inst_param(run_launcher, 'run_launcher', RunLauncher)

    def resolve_name(self, _graphene_info):
        return self._run_launcher.__class__.__name__


class DauhphinInstance(dauphin.ObjectType):
    class Meta(object):
        name = 'Instance'

    info = dauphin.NonNull(dauphin.String)
    runLauncher = dauphin.Field('RunLauncher')
    disableRunStart = dauphin.NonNull(dauphin.Boolean)

    def __init__(self, instance):
        self._instance = check.inst_param(instance, 'instance', DagsterInstance)

    def resolve_info(self, _graphene_info):
        return self._instance.info_str()

    def resolve_runLauncher(self, _graphene_info):
        return (
            DauhphinRunLauncher(self._instance.run_launcher)
            if self._instance.run_launcher
            else None
        )

    def resolve_disableRunStart(self, _graphene_info):
        execution_manager_settings = self._instance.dagit_settings.get('execution_manager')
        if not execution_manager_settings:
            return False
        return execution_manager_settings.get('disabled', False)
