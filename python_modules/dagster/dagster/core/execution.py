'''
Naming conventions:

For public functions:

execute_*

These represent functions which do purely in-memory compute. They will evaluate expectations
the core transform, and exercise all logging and metrics tracking (outside of outputs), but they
will not invoke *any* outputs (and their APIs don't allow the user to).


'''

# too many lines
# pylint: disable=C0302

from collections import defaultdict, OrderedDict
from contextlib import contextmanager
import inspect
import itertools
import time
import sys

from contextlib2 import ExitStack
from dagster import check
from dagster.utils import merge_dicts
from dagster.utils.error import serializable_error_info_from_exc_info
from dagster.utils.logging import define_colored_console_logger

from .definitions import PipelineDefinition, Solid, create_environment_type
from .definitions.resource import ResourcesBuilder, ResourcesSource
from .definitions.utils import DEFAULT_OUTPUT
from .definitions.environment_configs import construct_environment_config

from .execution_context import (
    RunConfig,
    InProcessExecutorConfig,
    MultiprocessExecutorConfig,
    SystemPipelineExecutionContextData,
    SystemPipelineExecutionContext,
)

from .errors import (
    DagsterError,
    DagsterExecutionStepNotFoundError,
    DagsterInvariantViolationError,
    DagsterRunNotFoundError,
    DagsterStepOutputNotFoundError,
    DagsterUserCodeExecutionError,
    DagsterContextFunctionError,
    DagsterResourceFunctionError,
    user_code_error_boundary,
)

from .events import DagsterEvent, DagsterEventType, PipelineInitFailureData
from .events.logging import construct_event_logger

from .execution_plan.plan import ExecutionPlan
from .execution_plan.objects import StepKind
from .engine.engine_multiprocessing import MultiprocessingEngine
from .engine.engine_inprocess import InProcessEngine

from .init_context import InitContext, InitResourceContext

from .intermediates_manager import (
    ObjectStoreIntermediatesManager,
    InMemoryIntermediatesManager,
    IntermediatesManager,
)

from .log import DagsterLog

from .object_store import FileSystemObjectStore, construct_type_storage_plugin_registry

from .runs import (
    DagsterRunMeta,
    FileSystemRunStorage,
    InMemoryRunStorage,
    RunStorage,
    RunStorageMode,
)

from .system_config.objects import EnvironmentConfig

from .types.evaluator import EvaluationError, evaluate_config_value, friendly_string_for_error

from .user_context import ExecutionContext


class PipelineExecutionResult(object):
    '''Result of execution of the whole pipeline. Returned eg by :py:func:`execute_pipeline`.
    '''

    def __init__(self, pipeline, run_id, event_list, reconstruct_context):
        self.pipeline = check.inst_param(pipeline, 'pipeline', PipelineDefinition)
        self.run_id = check.str_param(run_id, 'run_id')
        self.event_list = check.list_param(event_list, 'step_event_list', of_type=DagsterEvent)
        self.reconstruct_context = check.callable_param(reconstruct_context, 'reconstruct_context')

        solid_result_dict = self._context_solid_result_dict(event_list)

        self.solid_result_dict = solid_result_dict
        self.solid_result_list = list(self.solid_result_dict.values())

    def _context_solid_result_dict(self, event_list):
        solid_set = set()
        solid_order = []
        step_events_by_solid_by_kind = defaultdict(lambda: defaultdict(list))
        step_event_list = [event for event in event_list if event.is_step_event]
        for step_event in step_event_list:
            solid_name = step_event.solid_name
            if solid_name not in solid_set:
                solid_order.append(solid_name)
                solid_set.add(solid_name)

            step_events_by_solid_by_kind[solid_name][step_event.step_kind].append(step_event)

        solid_result_dict = OrderedDict()

        for solid_name in solid_order:
            solid_result_dict[solid_name] = SolidExecutionResult(
                self.pipeline.solid_named(solid_name),
                dict(step_events_by_solid_by_kind[solid_name]),
                self.reconstruct_context,
            )
        return solid_result_dict

    @property
    def success(self):
        '''Whether the pipeline execution was successful at all steps'''
        return all([not event.is_failure for event in self.event_list])

    @property
    def step_event_list(self):
        return [event for event in self.event_list if event.is_step_event]

    def result_for_solid(self, name):
        '''Get a :py:class:`SolidExecutionResult` for a given solid name.
        '''
        check.str_param(name, 'name')

        if not self.pipeline.has_solid_named(name):
            raise DagsterInvariantViolationError(
                'Try to get result for solid {name} in {pipeline}. No such solid.'.format(
                    name=name, pipeline=self.pipeline.display_name
                )
            )

        if name not in self.solid_result_dict:
            raise DagsterInvariantViolationError(
                'Did not find result for solid {name} in pipeline execution result'.format(
                    name=name
                )
            )

        return self.solid_result_dict[name]


class SolidExecutionResult(object):
    '''Execution result for one solid of the pipeline.

    Attributes:
      context (ExecutionContext): ExecutionContext of that particular Pipeline run.
      solid (SolidDefinition): Solid for which this result is
    '''

    def __init__(self, solid, step_events_by_kind, reconstruct_context):
        self.solid = check.inst_param(solid, 'solid', Solid)
        self.step_events_by_kind = check.dict_param(
            step_events_by_kind, 'step_events_by_kind', key_type=StepKind, value_type=list
        )
        self.reconstruct_context = check.callable_param(reconstruct_context, 'reconstruct_context')

    @property
    def transform(self):
        check.invariant(len(self.step_events_by_kind[StepKind.TRANSFORM]) == 1)
        return self.step_events_by_kind[StepKind.TRANSFORM][0]

    @property
    def transforms(self):
        return self.step_events_by_kind.get(StepKind.TRANSFORM, [])

    @property
    def input_expectations(self):
        return self.step_events_by_kind.get(StepKind.INPUT_EXPECTATION, [])

    @property
    def output_expectations(self):
        return self.step_events_by_kind.get(StepKind.OUTPUT_EXPECTATION, [])

    @property
    def success(self):
        '''Whether the solid execution was successful'''
        any_success = False
        for step_event in itertools.chain(
            self.input_expectations, self.output_expectations, self.transforms
        ):
            if step_event.event_type == DagsterEventType.STEP_FAILURE:
                return False
            if step_event.event_type == DagsterEventType.STEP_SUCCESS:
                any_success = True

        return any_success

    @property
    def skipped(self):
        '''Whether the solid execution was skipped'''
        return all(
            [
                step_event.event_type == DagsterEventType.STEP_SKIPPED
                for step_event in itertools.chain(
                    self.input_expectations, self.output_expectations, self.transforms
                )
            ]
        )

    @property
    def transformed_values(self):
        '''Return dictionary of transformed results, with keys being output names.
        Returns None if execution result isn't a success.

        Reconstructs the pipeline context to materialize values.
        '''
        if self.success and self.transforms:
            with self.reconstruct_context() as context:
                values = {
                    result.step_output_data.output_name: self._get_value(
                        context, result.step_output_data
                    )
                    for result in self.transforms
                    if result.is_successful_output
                }
            return values
        else:
            return None

    def transformed_value(self, output_name=DEFAULT_OUTPUT):
        '''Returns transformed value either for DEFAULT_OUTPUT or for the output
        given as output_name. Returns None if execution result isn't a success.

        Reconstructs the pipeline context to materialize value.
        '''
        check.str_param(output_name, 'output_name')

        if not self.solid.definition.has_output(output_name):
            raise DagsterInvariantViolationError(
                '{output_name} not defined in solid {solid}'.format(
                    output_name=output_name, solid=self.solid.name
                )
            )

        if self.success:
            for result in self.transforms:
                if (
                    result.is_successful_output
                    and result.step_output_data.output_name == output_name
                ):
                    with self.reconstruct_context() as context:
                        value = self._get_value(context, result.step_output_data)
                    return value

            raise DagsterInvariantViolationError(
                (
                    'Did not find result {output_name} in solid {self.solid.name} '
                    'execution result'
                ).format(output_name=output_name, self=self)
            )
        else:
            return None

    def _get_value(self, context, step_output_data):
        return context.intermediates_manager.get_intermediate(
            context=context,
            runtime_type=self.solid.output_def_named(step_output_data.output_name).runtime_type,
            step_output_handle=step_output_data.step_output_handle,
        )

    @property
    def failure_data(self):
        '''Returns the failing step's data that happened during this solid's execution, if any'''
        for result in itertools.chain(
            self.input_expectations, self.output_expectations, self.transforms
        ):
            if result.event_type == DagsterEventType.STEP_FAILURE:
                return result.step_failure_data


def check_run_config_param(run_config):
    return (
        check.inst_param(run_config, 'run_config', RunConfig)
        if run_config
        else RunConfig(executor_config=InProcessExecutorConfig())
    )


def create_execution_plan(pipeline, environment_dict=None):
    check.inst_param(pipeline, 'pipeline', PipelineDefinition)
    environment_dict = check.opt_dict_param(environment_dict, 'environment_dict', key_type=str)
    environment_config = create_environment_config(pipeline, environment_dict)
    return ExecutionPlan.build(pipeline, environment_config)


def get_logging_tags(user_context_params, run_config, pipeline):
    check.opt_inst_param(user_context_params, 'user_context_params', ExecutionContext)
    check.opt_inst_param(run_config, 'run_config', RunConfig)
    check.inst_param(pipeline, 'pipeline', PipelineDefinition)

    user_tags = user_context_params.tags if user_context_params else {}
    run_tags = run_config.tags if run_config else {}

    base_tags = merge_dicts({'pipeline': pipeline.name}, user_tags)

    if run_config and run_config.tags:
        user_keys = set(user_tags.keys())
        provided_keys = set(run_tags.keys())
        if not user_keys.isdisjoint(provided_keys):
            raise DagsterInvariantViolationError(
                (
                    'You have specified tags and user-defined tags '
                    'that overlap. User keys: {user_keys}. Reentrant keys: '
                    '{provided_keys}.'
                ).format(user_keys=user_keys, provided_keys=provided_keys)
            )

        return merge_dicts(base_tags, run_tags)
    else:
        return base_tags


def _ensure_gen(thing_or_gen):
    if not inspect.isgenerator(thing_or_gen):

        def _gen_thing():
            yield thing_or_gen

        return _gen_thing()

    return thing_or_gen


@contextmanager
def user_code_context_manager(user_fn, error_cls, msg):
    '''Wraps the output of a user provided function that may yield or return a value and
    returns a generator that asserts it only yields a single value.
    '''
    check.callable_param(user_fn, 'user_fn')
    check.subclass_param(error_cls, 'error_cls', DagsterUserCodeExecutionError)

    with user_code_error_boundary(error_cls, msg):
        thing_or_gen = user_fn()
        gen = _ensure_gen(thing_or_gen)

        try:
            thing = next(gen)
        except StopIteration:
            check.failed('Must yield one item. You did not yield anything.')

        yield thing

        stopped = False

        try:
            next(gen)
        except StopIteration:
            stopped = True

        check.invariant(stopped, 'Must yield one item. Yielded more than one item')


def construct_run_storage(run_config, environment_config):
    '''
    Construct the run storage for this pipeline. Our rules are the following:

    If the RunConfig has a storage_mode provided, we use that.

    Then we fallback to environment config.

    If there is no config, we default to in memory storage. This is mostly so
    that tests default to in-memory.
    '''
    check.inst_param(run_config, 'run_config', RunConfig)
    check.inst_param(environment_config, 'environment_config', EnvironmentConfig)

    if run_config.storage_mode:
        if run_config.storage_mode == RunStorageMode.FILESYSTEM:
            return FileSystemRunStorage()
        elif run_config.storage_mode == RunStorageMode.IN_MEMORY:
            return InMemoryRunStorage()
        elif run_config.storage_mode == RunStorageMode.S3:
            # TODO: Revisit whether we want to use S3 run storage
            return FileSystemRunStorage()
        else:
            check.failed('Unexpected enum {}'.format(run_config.storage_mode))
    elif environment_config.storage.storage_mode == 'filesystem':
        return FileSystemRunStorage()
    elif environment_config.storage.storage_mode == 'in_memory':
        return InMemoryRunStorage()
    elif environment_config.storage.storage_mode == 's3':
        # TODO: Revisit whether we want to use S3 run storage
        return FileSystemRunStorage()
    elif environment_config.storage.storage_mode is None:
        return InMemoryRunStorage()
    else:
        raise DagsterInvariantViolationError(
            'Invalid storage specified {}'.format(environment_config.storage.storage_mode)
        )


def ensure_dagster_aws_requirements():
    try:
        import dagster_aws
    except (ImportError, ModuleNotFoundError):
        raise check.CheckError(
            'dagster_aws must be available for import in order to make use of an S3ObjectStore'
        )

    return dagster_aws


def construct_intermediates_manager(run_config, environment_config, pipeline_def):
    check.inst_param(run_config, 'run_config', RunConfig)
    check.inst_param(environment_config, 'environment_config', EnvironmentConfig)
    check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition)

    if run_config.storage_mode:
        if run_config.storage_mode == RunStorageMode.FILESYSTEM:
            return ObjectStoreIntermediatesManager(
                FileSystemObjectStore(
                    run_config.run_id,
                    construct_type_storage_plugin_registry(pipeline_def, RunStorageMode.FILESYSTEM),
                )
            )
        elif run_config.storage_mode == RunStorageMode.IN_MEMORY:
            return InMemoryIntermediatesManager()
        elif run_config.storage_mode == RunStorageMode.S3:
            _dagster_aws = ensure_dagster_aws_requirements()
            from dagster_aws.s3.object_store import S3ObjectStore

            return ObjectStoreIntermediatesManager(
                S3ObjectStore(
                    environment_config.storage.storage_config['s3_bucket'],
                    run_config.run_id,
                    construct_type_storage_plugin_registry(pipeline_def, RunStorageMode.S3),
                )
            )
        else:
            check.failed('Unexpected enum {}'.format(run_config.storage_mode))
    elif environment_config.storage.storage_mode == 'filesystem':
        return ObjectStoreIntermediatesManager(
            FileSystemObjectStore(
                run_config.run_id,
                construct_type_storage_plugin_registry(pipeline_def, RunStorageMode.FILESYSTEM),
            )
        )
    elif environment_config.storage.storage_mode == 'in_memory':
        return InMemoryIntermediatesManager()
    elif environment_config.storage.storage_mode == 's3':
        _dagster_aws = ensure_dagster_aws_requirements()
        from dagster_aws.s3.object_store import S3ObjectStore

        return ObjectStoreIntermediatesManager(
            S3ObjectStore(
                environment_config.storage.storage_config['s3_bucket'],
                run_config.run_id,
                construct_type_storage_plugin_registry(pipeline_def, RunStorageMode.S3),
            )
        )
    elif environment_config.storage.storage_mode is None:
        return InMemoryIntermediatesManager()
    else:
        raise DagsterInvariantViolationError(
            'Invalid storage specified {}'.format(environment_config.storage.storage_mode)
        )


@contextmanager
def yield_pipeline_execution_context(pipeline_def, environment_dict, run_config):
    check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition)
    check.dict_param(environment_dict, 'environment_dict', key_type=str)
    check.inst_param(run_config, 'run_config', RunConfig)

    environment_config = create_environment_config(pipeline_def, environment_dict)
    intermediates_manager = construct_intermediates_manager(
        run_config, environment_config, pipeline_def
    )
    with _pipeline_execution_context_manager(
        pipeline_def, environment_config, run_config, intermediates_manager
    ) as context:
        yield context


@contextmanager
def _pipeline_execution_context_manager(
    pipeline_def, environment_config, run_config, intermediates_manager
):
    check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition)
    check.inst_param(environment_config, 'environment_config', EnvironmentConfig)
    check.inst_param(run_config, 'run_config', RunConfig)
    check.inst_param(intermediates_manager, 'intermediates_manager', IntermediatesManager)

    context_definition = pipeline_def.context_definitions[environment_config.context.name]

    run_storage = construct_run_storage(run_config, environment_config)

    run_storage.write_dagster_run_meta(
        DagsterRunMeta(
            run_id=run_config.run_id, timestamp=time.time(), pipeline_name=pipeline_def.name
        )
    )

    init_context = InitContext(
        context_config=environment_config.context.config,
        pipeline_def=pipeline_def,
        run_id=run_config.run_id,
    )

    try:
        with user_code_context_manager(
            lambda: context_definition.context_fn(init_context),
            DagsterContextFunctionError,
            'Error executing context_fn on ContextDefinition {name}'.format(
                name=environment_config.context.name
            ),
        ) as execution_context:
            check.inst(execution_context, ExecutionContext)

            with _create_resources(
                pipeline_def,
                context_definition,
                environment_config,
                execution_context,
                run_config.run_id,
            ) as resources:

                yield construct_pipeline_execution_context(
                    run_config,
                    execution_context,
                    pipeline_def,
                    resources,
                    environment_config,
                    run_storage,
                    intermediates_manager,
                )

    except DagsterError as dagster_error:
        user_facing_exc_info = (
            # pylint does not know original_exc_info exists is is_user_code_error is true
            # pylint: disable=no-member
            dagster_error.original_exc_info
            if dagster_error.is_user_code_error
            else sys.exc_info()
        )

        if run_config.executor_config.raise_on_error:
            raise dagster_error

        error_info = serializable_error_info_from_exc_info(user_facing_exc_info)
        yield DagsterEvent.pipeline_init_failure(
            pipeline_name=pipeline_def.name,
            failure_data=PipelineInitFailureData(error=error_info),
            log=_create_context_free_log(run_config, pipeline_def),
        )


def construct_pipeline_execution_context(
    run_config,
    execution_context,
    pipeline,
    resources,
    environment_config,
    run_storage,
    intermediates_manager,
):
    check.inst_param(run_config, 'run_config', RunConfig)
    check.inst_param(execution_context, 'execution_context', ExecutionContext)
    check.inst_param(pipeline, 'pipeline', PipelineDefinition)
    check.opt_inst_param(resources, 'resources', ResourcesBuilder)
    check.inst_param(environment_config, 'environment_config', EnvironmentConfig)
    check.inst_param(run_storage, 'run_storage', RunStorage)
    check.inst_param(intermediates_manager, 'intermediates_manager', IntermediatesManager)

    loggers = _create_loggers(run_config, execution_context)
    logging_tags = get_logging_tags(execution_context, run_config, pipeline)
    log = DagsterLog(run_config.run_id, logging_tags, loggers)

    return SystemPipelineExecutionContext(
        SystemPipelineExecutionContextData(
            pipeline_def=pipeline,
            run_config=run_config,
            resources=resources,
            environment_config=environment_config,
            run_storage=run_storage,
            intermediates_manager=intermediates_manager,
        ),
        logging_tags=logging_tags,
        log=log,
    )


def _create_loggers(run_config, execution_context):
    check.inst_param(run_config, 'run_config', RunConfig)
    check.inst_param(execution_context, 'execution_context', ExecutionContext)

    if run_config.event_callback:
        return execution_context.loggers + [construct_event_logger(run_config.event_callback)]
    elif run_config.loggers:
        return execution_context.loggers + run_config.loggers
    else:
        return execution_context.loggers


def _create_context_free_log(run_config, pipeline_def):
    '''In the event of pipeline initialization failure, we want to be able to log the failure
    without a dependency on the ExecutionContext to initialize DagsterLog
    '''
    check.inst_param(run_config, 'run_config', RunConfig)
    check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition)

    # Use the default logger
    loggers = [define_colored_console_logger('dagster')]
    if run_config.event_callback:
        loggers += [construct_event_logger(run_config.event_callback)]
    elif run_config.loggers:
        loggers += run_config.loggers

    return DagsterLog(run_config.run_id, get_logging_tags(None, run_config, pipeline_def), loggers)


@contextmanager
def _create_resources(pipeline_def, context_def, environment, execution_context, run_id):
    if not context_def.resources:
        yield ResourcesBuilder(
            execution_context.resources, ResourcesSource.CUSTOM_EXECUTION_CONTEXT
        )
        return

    resources = {}
    check.invariant(
        not execution_context.resources,
        (
            'If resources explicitly specified on context definition, the context '
            'creation function should not return resources as a property of the '
            'ExecutionContext.'
        ),
    )

    # See https://bit.ly/2zIXyqw
    # The "ExitStack" allows one to stack up N context managers and then yield
    # something. We do this so that resources can cleanup after themselves. We
    # can potentially have many resources so we need to use this abstraction.
    with ExitStack() as stack:
        for resource_name in context_def.resources.keys():
            user_fn = _create_resource_fn_lambda(
                pipeline_def, context_def, resource_name, environment, run_id
            )

            resource_obj = stack.enter_context(
                user_code_context_manager(
                    user_fn,
                    DagsterResourceFunctionError,
                    'Error executing resource_fn on ResourceDefinition {name}'.format(
                        name=resource_name
                    ),
                )
            )

            resources[resource_name] = resource_obj
        yield ResourcesBuilder(resources, ResourcesSource.PIPELINE_CONTEXT_DEF)


def _create_resource_fn_lambda(
    pipeline_def, context_definition, resource_name, environment, run_id
):
    resource_def = context_definition.resources[resource_name]
    # Need to do default values
    resource_config = environment.context.resources.get(resource_name, {}).get('config')
    return lambda: resource_def.resource_fn(
        InitResourceContext(
            pipeline_def=pipeline_def,
            resource_def=resource_def,
            context_config=environment.context.config,
            resource_config=resource_config,
            run_id=run_id,
        )
    )


def _execute_pipeline_iterator(context_or_failure_event):
    # Due to use of context managers, if the user land code in context or resource init fails
    # we can get either a pipeline_context or the failure event here.
    if (
        isinstance(context_or_failure_event, DagsterEvent)
        and context_or_failure_event.event_type == DagsterEventType.PIPELINE_INIT_FAILURE
    ):
        yield context_or_failure_event
        return

    pipeline_context = context_or_failure_event
    check.inst_param(pipeline_context, 'pipeline_context', SystemPipelineExecutionContext)
    yield DagsterEvent.pipeline_start(pipeline_context)

    execution_plan = ExecutionPlan.build(
        pipeline_context.pipeline_def, pipeline_context.environment_config
    )

    steps = execution_plan.topological_steps()

    if not steps:
        pipeline_context.log.debug(
            'Pipeline {pipeline} has no nodes and no execution will happen'.format(
                pipeline=pipeline_context.pipeline_def.display_name
            )
        )
        yield DagsterEvent.pipeline_success(pipeline_context)
        return

    _setup_reexecution(pipeline_context.run_config, pipeline_context, execution_plan)

    pipeline_context.log.debug(
        'About to execute the compute node graph in the following order {order}'.format(
            order=[step.key for step in steps]
        )
    )

    check.invariant(len(steps[0].step_inputs) == 0)

    pipeline_success = True

    try:
        for event in invoke_executor_on_plan(
            pipeline_context, execution_plan, pipeline_context.run_config.step_keys_to_execute
        ):
            if event.is_step_failure:
                pipeline_success = False
            yield event
    finally:
        if pipeline_success:
            yield DagsterEvent.pipeline_success(pipeline_context)
        else:
            yield DagsterEvent.pipeline_failure(pipeline_context)


def execute_pipeline_iterator(pipeline, environment_dict=None, run_config=None):
    '''Returns iterator that yields :py:class:`SolidExecutionResult` for each
    solid executed in the pipeline.

    This is intended to allow the caller to do things between each executed
    node. For the 'synchronous' API, see :py:func:`execute_pipeline`.

    Parameters:
      pipeline (PipelineDefinition): Pipeline to run
      environment_dict (dict): The enviroment configuration that parameterizes this run
      run_config (RunConfig): Configuration for how this pipeline will be executed

    Returns:
      Iterator[DagsterEvent]
    '''
    check.inst_param(pipeline, 'pipeline', PipelineDefinition)
    environment_dict = check.opt_dict_param(environment_dict, 'environment_dict')
    run_config = check_run_config_param(run_config)
    environment_config = create_environment_config(pipeline, environment_dict)
    intermediates_manager = construct_intermediates_manager(
        run_config, environment_config, pipeline
    )

    with _pipeline_execution_context_manager(
        pipeline, environment_config, run_config, intermediates_manager
    ) as pipeline_context:
        return _execute_pipeline_iterator(pipeline_context)


def execute_pipeline(pipeline, environment_dict=None, run_config=None):
    '''
    "Synchronous" version of :py:func:`execute_pipeline_iterator`.

    Note: raise_on_error is very useful in testing contexts when not testing for error
    conditions

    Parameters:
      pipeline (PipelineDefinition): Pipeline to run
      environment_dict (dict): The enviroment configuration that parameterizes this run
      run_config (RunConfig): Configuration for how this pipeline will be executed

    Returns:
      :py:class:`PipelineExecutionResult`
    '''

    check.inst_param(pipeline, 'pipeline', PipelineDefinition)
    environment_dict = check.opt_dict_param(environment_dict, 'environment_dict')
    run_config = check_run_config_param(run_config)
    environment_config = create_environment_config(pipeline, environment_dict)
    intermediates_manager = construct_intermediates_manager(
        run_config, environment_config, pipeline
    )

    with _pipeline_execution_context_manager(
        pipeline, environment_config, run_config, intermediates_manager
    ) as pipeline_context:
        event_list = list(_execute_pipeline_iterator(pipeline_context))

    return PipelineExecutionResult(
        pipeline,
        run_config.run_id,
        event_list,
        lambda: _pipeline_execution_context_manager(
            pipeline, environment_config, run_config, intermediates_manager
        ),
    )


class PipelineConfigEvaluationError(Exception):
    def __init__(self, pipeline, errors, config_value, *args, **kwargs):
        self.pipeline = check.inst_param(pipeline, 'pipeline', PipelineDefinition)
        self.errors = check.list_param(errors, 'errors', of_type=EvaluationError)
        self.config_value = config_value

        error_msg = 'Pipeline "{pipeline}" config errors:'.format(pipeline=pipeline.name)

        error_messages = []

        for i_error, error in enumerate(self.errors):
            error_message = friendly_string_for_error(error)
            error_messages.append(error_message)
            error_msg += '\n    Error {i_error}: {error_message}'.format(
                i_error=i_error + 1, error_message=error_message
            )

        self.message = error_msg
        self.error_messages = error_messages

        super(PipelineConfigEvaluationError, self).__init__(error_msg, *args, **kwargs)


def invoke_executor_on_plan(pipeline_context, execution_plan, step_keys_to_execute=None):
    if step_keys_to_execute:
        for step_key in step_keys_to_execute:
            if not execution_plan.has_step(step_key):
                raise DagsterExecutionStepNotFoundError(step_key=step_key)

    # Toggle engine based on executor config supplied by the pipeline context
    def get_engine_for_config(cfg):
        if isinstance(cfg, InProcessExecutorConfig):
            return InProcessEngine
        elif isinstance(cfg, MultiprocessExecutorConfig):
            return MultiprocessingEngine
        else:
            check.failed('Unsupported config {}'.format(cfg))

    # Engine execution returns a generator of yielded events, so returning here means this function
    # also returns a generator
    return get_engine_for_config(pipeline_context.executor_config).execute(
        pipeline_context, execution_plan, step_keys_to_execute
    )


def _check_reexecution_config(pipeline_context, execution_plan, run_config):
    check.invariant(pipeline_context.run_storage)

    if not pipeline_context.run_storage.is_persistent:
        raise DagsterInvariantViolationError(
            'Cannot perform reexecution with non persistent run storage.'
        )

    previous_run_id = run_config.reexecution_config.previous_run_id

    if not pipeline_context.run_storage.has_run(previous_run_id):
        raise DagsterRunNotFoundError(
            'Run id {} set as previous run id was not found in run storage'.format(previous_run_id),
            invalid_run_id=previous_run_id,
        )

    for step_output_handle in run_config.reexecution_config.step_output_handles:
        if not execution_plan.has_step(step_output_handle.step_key):
            raise DagsterExecutionStepNotFoundError(
                (
                    'Step {step_key} was specified as a step from a previous run. '
                    'It does not exist.'
                ).format(step_key=step_output_handle.step_key),
                step_key=step_output_handle.step_key,
            )

        step = execution_plan.get_step_by_key(step_output_handle.step_key)
        if not step.has_step_output(step_output_handle.output_name):
            raise DagsterStepOutputNotFoundError(
                (
                    'You specified a step_output_handle in the ReexecutionConfig that does '
                    'not exist: Step {step_key} does not have output {output_name}.'
                ).format(
                    step_key=step_output_handle.step_key, output_name=step_output_handle.output_name
                ),
                step_key=step_output_handle.step_key,
                output_name=step_output_handle.output_name,
            )


def execute_plan(execution_plan, environment_dict=None, run_config=None, step_keys_to_execute=None):
    check.inst_param(execution_plan, 'execution_plan', ExecutionPlan)
    environment_dict = check.opt_dict_param(environment_dict, 'environment_dict')
    run_config = check_run_config_param(run_config)
    check.opt_list_param(step_keys_to_execute, 'step_keys_to_execute', of_type=str)

    if step_keys_to_execute:
        for step_key in step_keys_to_execute:
            if not execution_plan.has_step(step_key):
                raise DagsterExecutionStepNotFoundError(
                    'Execution plan does not contain step "{}"'.format(step_key), step_key=step_key
                )

    with yield_pipeline_execution_context(
        execution_plan.pipeline_def, environment_dict, run_config
    ) as pipeline_context:

        _setup_reexecution(run_config, pipeline_context, execution_plan)

        return list(invoke_executor_on_plan(pipeline_context, execution_plan, step_keys_to_execute))


def _setup_reexecution(run_config, pipeline_context, execution_plan):
    if run_config.reexecution_config:
        _check_reexecution_config(pipeline_context, execution_plan, run_config)

        for step_output_handle in run_config.reexecution_config.step_output_handles:
            pipeline_context.intermediates_manager.copy_intermediate_from_prev_run(
                pipeline_context, run_config.reexecution_config.previous_run_id, step_output_handle
            )


def create_environment_config(pipeline, environment_dict=None):
    check.inst_param(pipeline, 'pipeline', PipelineDefinition)
    check.opt_dict_param(environment_dict, 'environment')

    environment_type = create_environment_type(pipeline)

    result = evaluate_config_value(environment_type, environment_dict)

    if not result.success:
        raise PipelineConfigEvaluationError(pipeline, result.errors, environment_dict)

    return construct_environment_config(result.value)


def step_output_event_filter(pipe_iterator):
    for step_event in pipe_iterator:
        if step_event.is_successful_output:
            yield step_event


class ExecutionSelector(object):
    def __init__(self, name, solid_subset=None):
        self.name = check.str_param(name, 'name')
        if solid_subset is None:
            self.solid_subset = None
        else:
            self.solid_subset = check.opt_list_param(solid_subset, 'solid_subset', of_type=str)
