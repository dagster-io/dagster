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

from contextlib2 import ExitStack
from dagster import check
from dagster.utils import merge_dicts

from .definitions import PipelineDefinition, Solid
from .definitions.utils import DEFAULT_OUTPUT
from .definitions.environment_configs import construct_environment_config

from .execution_context import (
    RunConfig,
    InProcessExecutorConfig,
    MultiprocessExecutorConfig,
    SystemPipelineExecutionContextData,
    SystemPipelineExecutionContext,
)

from .errors import DagsterInvariantViolationError

from .events import construct_event_logger

from .execution_plan.create import create_execution_plan_core

from .execution_plan.intermediates_manager import (
    FileSystemIntermediateManager,
    InMemoryIntermediatesManager,
)

from .execution_plan.objects import (
    ExecutionPlan,
    ExecutionStepEvent,
    ExecutionStepEventType,
    StepKind,
)

from .execution_plan.multiprocessing_engine import multiprocess_execute_plan

from .execution_plan.simple_engine import start_inprocess_executor

from .init_context import InitContext, InitResourceContext

from .log import DagsterLog

from .runs import DagsterRunMeta, FileSystemRunStorage, InMemoryRunStorage, RunStorageMode

from .system_config.objects import EnvironmentConfig

from .types.evaluator import EvaluationError, evaluate_config_value, friendly_string_for_error
from .types.marshal import FilePersistencePolicy

from .user_context import ExecutionContext


class PipelineExecutionResult(object):
    '''Result of execution of the whole pipeline. Returned eg by :py:func:`execute_pipeline`.

    Attributes:
        pipeline (PipelineDefinition): Pipeline that was executed
        context (ExecutionContext): ExecutionContext of that particular Pipeline run.
        result_list (list[SolidExecutionResult]): List of results for each pipeline solid.
    '''

    def __init__(self, pipeline, run_id, step_event_list):
        self.pipeline = check.inst_param(pipeline, 'pipeline', PipelineDefinition)
        self.run_id = check.str_param(run_id, 'run_id')
        self.step_event_list = check.list_param(
            step_event_list, 'step_event_list', of_type=ExecutionStepEvent
        )

        solid_result_dict = self._context_solid_result_dict(step_event_list)

        self.solid_result_dict = solid_result_dict
        self.solid_result_list = list(self.solid_result_dict.values())

    def _context_solid_result_dict(self, step_event_list):
        solid_set = set()
        solid_order = []
        step_events_by_solid_by_kind = defaultdict(lambda: defaultdict(list))

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
            )
        return solid_result_dict

    @property
    def success(self):
        '''Whether the pipeline execution was successful at all steps'''
        return all([not step_event.is_step_failure for step_event in self.step_event_list])

    def result_for_solid(self, name):
        '''Get a :py:class:`SolidExecutionResult` for a given solid name.

        Returns:
          SolidExecutionResult
        '''
        check.str_param(name, 'name')

        if not self.pipeline.has_solid(name):
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

    def __init__(self, solid, step_events_by_kind):
        self.solid = check.inst_param(solid, 'solid', Solid)
        self.step_events_by_kind = check.dict_param(
            step_events_by_kind, 'step_events_by_kind', key_type=StepKind, value_type=list
        )

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

    @staticmethod
    def from_step_events(pipeline_context, step_events):
        check.inst_param(pipeline_context, 'pipeline_context', SystemPipelineExecutionContext)
        step_events = check.list_param(step_events, 'step_events', ExecutionStepEvent)
        if step_events:
            step_events_by_kind = defaultdict(list)

            solid = None
            for result in step_events:
                if solid is None:
                    solid = result.step.solid
                check.invariant(result.step.solid is solid, 'Must all be from same solid')

            for result in step_events:
                step_events_by_kind[result.kind].append(result)

            return SolidExecutionResult(
                solid=step_events[0].step.solid, step_events_by_kind=dict(step_events_by_kind)
            )
        else:
            check.failed("Cannot create SolidExecutionResult from empty list")

    @property
    def success(self):
        '''Whether the solid execution was successful'''
        return all(
            [
                not step_event.is_step_failure
                for step_event in itertools.chain(
                    self.input_expectations, self.output_expectations, self.transforms
                )
            ]
        )

    @property
    def transformed_values(self):
        '''Return dictionary of transformed results, with keys being output names.
        Returns None if execution result isn't a success.'''
        if self.success and self.transforms:
            return {
                result.step_output_data.output_name: result.step_output_data.get_value()
                for result in self.transforms
            }
        else:
            return None

    def transformed_value(self, output_name=DEFAULT_OUTPUT):
        '''Returns transformed value either for DEFAULT_OUTPUT or for the output
        given as output_name. Returns None if execution result isn't a success'''
        check.str_param(output_name, 'output_name')

        if not self.solid.definition.has_output(output_name):
            raise DagsterInvariantViolationError(
                '{output_name} not defined in solid {solid}'.format(
                    output_name=output_name, solid=self.solid.name
                )
            )

        if self.success:
            for result in self.transforms:
                if result.step_output_data.output_name == output_name:
                    return result.step_output_data.get_value()
            raise DagsterInvariantViolationError(
                (
                    'Did not find result {output_name} in solid {self.solid.name} '
                    'execution result'
                ).format(output_name=output_name, self=self)
            )
        else:
            return None

    @property
    def failure_data(self):
        '''Returns the failing step's data that happened during this solid's execution, if any'''
        for result in itertools.chain(
            self.input_expectations, self.output_expectations, self.transforms
        ):
            if result.event_type == ExecutionStepEventType.STEP_FAILURE:
                return result.step_failure_data


def check_run_config_param(run_config):
    return (
        check.inst_param(run_config, 'run_config', RunConfig)
        if run_config
        else RunConfig(executor_config=InProcessExecutorConfig())
    )


def create_execution_plan(pipeline, environment_dict=None, run_config=None):
    check.inst_param(pipeline, 'pipeline', PipelineDefinition)
    environment_dict = check.opt_dict_param(environment_dict, 'environment_dict', key_type=str)
    run_config = check_run_config_param(run_config)
    check.inst_param(run_config, 'run_config', RunConfig)

    with yield_pipeline_execution_context(
        pipeline, environment_dict, run_config
    ) as pipeline_context:
        return create_execution_plan_core(pipeline_context)


def get_tags(user_context_params, run_config, pipeline):
    check.inst_param(user_context_params, 'user_context_params', ExecutionContext)
    check.opt_inst_param(run_config, 'run_config', RunConfig)
    check.inst_param(pipeline, 'pipeline', PipelineDefinition)

    base_tags = merge_dicts({'pipeline': pipeline.name}, user_context_params.tags)

    if run_config and run_config.tags:
        user_keys = set(user_context_params.tags.keys())
        provided_keys = set(run_config.tags.keys())
        if not user_keys.isdisjoint(provided_keys):
            raise DagsterInvariantViolationError(
                (
                    'You have specified tags and user-defined tags '
                    'that overlap. User keys: {user_keys}. Reentrant keys: '
                    '{provided_keys}.'
                ).format(user_keys=user_keys, provided_keys=provided_keys)
            )

        return merge_dicts(base_tags, run_config.tags)
    else:
        return base_tags


def _ensure_gen(thing_or_gen):
    if not inspect.isgenerator(thing_or_gen):

        def _gen_thing():
            yield thing_or_gen

        return _gen_thing()

    return thing_or_gen


@contextmanager
def as_ensured_single_gen(thing_or_gen):
    '''Wraps the output of a user provided function that may yield or return a value and
    returns a generator that asserts it only yields a single value.
    '''
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


def _create_persistence_strategy(persistence_config):
    check.dict_param(persistence_config, 'persistence_config', key_type=str)

    persistence_key, _config_value = list(persistence_config.items())[0]

    if persistence_key == 'file':
        return FilePersistencePolicy()
    else:
        check.failed('Unsupported persistence key: {}'.format(persistence_key))


def construct_run_storage(run_config, _init_context, environment_config):
    '''
    Construct the run storage for this pipeline. Our rules are the following:

    If the called has specified a run_storage_factory_fn, we use for creating
    the run storage.

    Then we fallback to config.

    If there is no config, we default to in memory storage. This is mostly so
    that tests default to in-memory.
    '''
    if run_config.storage_mode:
        if run_config.storage_mode == RunStorageMode.FILESYSTEM:
            return FileSystemRunStorage()
        elif run_config.storage_mode == RunStorageMode.IN_MEMORY:
            return InMemoryRunStorage()
        else:
            check.failed('Unexpectd enum {}'.format(run_config.storage_mode))
    elif environment_config.storage.name == 'filesystem':
        return FileSystemRunStorage()
    elif environment_config.storage.name == 'inmem':
        return InMemoryRunStorage()
    elif environment_config.storage.name is None:
        return InMemoryRunStorage()
    else:
        raise DagsterInvariantViolationError(
            'Invalid storage specified {}'.format(environment_config.storage.name)
        )


def construct_intermediates_manager(run_config, init_context, environment_config):

    if run_config.storage_mode:
        if run_config.storage_mode == RunStorageMode.FILESYSTEM:
            return FileSystemIntermediateManager(init_context.run_id)
        elif run_config.storage_mode == RunStorageMode.IN_MEMORY:
            return InMemoryIntermediatesManager()
        else:
            check.failed('Unexpectd enum {}'.format(run_config.storage_mode))
    elif environment_config.storage.name == 'filesystem':

        return FileSystemIntermediateManager(init_context.run_id)
    elif environment_config.storage.name == 'inmem':
        return InMemoryIntermediatesManager()
    elif environment_config.storage.name is None:
        return InMemoryIntermediatesManager()
    else:
        raise DagsterInvariantViolationError(
            'Invalid storage specified {}'.format(environment_config.storage.name)
        )


@contextmanager
def yield_pipeline_execution_context(pipeline_def, environment_dict, run_config):
    check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition)
    check.dict_param(environment_dict, 'environment_dict', key_type=str)
    check.inst_param(run_config, 'run_config', RunConfig)

    environment_config = create_environment_config(pipeline_def, environment_dict)

    context_definition = pipeline_def.context_definitions[environment_config.context.name]

    init_context = InitContext(
        context_config=environment_config.context.config,
        pipeline_def=pipeline_def,
        run_id=run_config.run_id,
    )

    run_storage = construct_run_storage(run_config, init_context, environment_config)

    run_storage.write_dagster_run_meta(
        DagsterRunMeta(
            run_id=run_config.run_id, timestamp=time.time(), pipeline_name=pipeline_def.name
        )
    )

    ec_or_gen = context_definition.context_fn(init_context)

    with as_ensured_single_gen(ec_or_gen) as execution_context:
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
                construct_intermediates_manager(run_config, init_context, environment_config),
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
    check.inst_param(environment_config, 'environment_config', EnvironmentConfig)

    loggers = _create_loggers(run_config, execution_context)
    tags = get_tags(execution_context, run_config, pipeline)
    log = DagsterLog(run_config.run_id, tags, loggers)

    return SystemPipelineExecutionContext(
        SystemPipelineExecutionContextData(
            pipeline_def=pipeline,
            run_config=run_config,
            resources=resources,
            environment_config=environment_config,
            persistence_strategy=_create_persistence_strategy(
                environment_config.context.persistence
            ),
            run_storage=run_storage,
            intermediates_manager=intermediates_manager,
        ),
        tags=tags,
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


@contextmanager
def _create_resources(pipeline_def, context_def, environment, execution_context, run_id):
    if not context_def.resources:
        yield execution_context.resources
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
            resource_obj_or_gen = get_resource_or_gen(
                pipeline_def, context_def, resource_name, environment, run_id
            )

            resource_obj = stack.enter_context(as_ensured_single_gen(resource_obj_or_gen))

            resources[resource_name] = resource_obj

        context_name = environment.context.name

        resources_type = pipeline_def.context_definitions[context_name].resources_type
        yield resources_type(**resources)


def get_resource_or_gen(pipeline_def, context_definition, resource_name, environment, run_id):
    resource_def = context_definition.resources[resource_name]
    # Need to do default values
    resource_config = environment.context.resources.get(resource_name, {}).get('config')
    return resource_def.resource_fn(
        InitResourceContext(
            pipeline_def=pipeline_def,
            resource_def=resource_def,
            context_config=environment.context.config,
            resource_config=resource_config,
            run_id=run_id,
        )
    )


def execute_pipeline_iterator(pipeline, environment_dict=None, run_config=None):
    '''Returns iterator that yields :py:class:`SolidExecutionResult` for each
    solid executed in the pipeline.

    This is intended to allow the caller to do things between each executed
    node. For the 'synchronous' API, see :py:func:`execute_pipeline`.

    Parameters:
      pipeline (PipelineDefinition): pipeline to run
      execution (ExecutionContext): execution context of the run
    '''
    check.inst_param(pipeline, 'pipeline', PipelineDefinition)
    environment_dict = check.opt_dict_param(environment_dict, 'environment_dict')
    run_config = check_run_config_param(run_config)

    with yield_pipeline_execution_context(
        pipeline, environment_dict, run_config
    ) as pipeline_context:

        pipeline_context.events.pipeline_start()

        execution_plan = create_execution_plan_core(pipeline_context)

        steps = execution_plan.topological_steps()

        if not steps:
            pipeline_context.log.debug(
                'Pipeline {pipeline} has no nodes and no execution will happen'.format(
                    pipeline=pipeline.display_name
                )
            )
            pipeline_context.events.pipeline_success()
            return

        pipeline_context.log.debug(
            'About to execute the compute node graph in the following order {order}'.format(
                order=[step.key for step in steps]
            )
        )

        check.invariant(len(steps[0].step_inputs) == 0)

        pipeline_success = True

        for step_event in invoke_executor_on_plan(pipeline_context, execution_plan):
            if step_event.is_step_failure:
                pipeline_success = False
            yield step_event

        if pipeline_success:
            pipeline_context.events.pipeline_success()
        else:
            pipeline_context.events.pipeline_failure()


def execute_pipeline(pipeline, environment_dict=None, run_config=None):
    '''
    "Synchronous" version of :py:func:`execute_pipeline_iterator`.

    Note: throw_on_user_error is very useful in testing contexts when not testing for error
    conditions

    Parameters:
      pipeline (PipelineDefinition): Pipeline to run
      environment (dict): The enviroment that parameterizes this run

    Returns:
      PipelineExecutionResult
    '''

    check.inst_param(pipeline, 'pipeline', PipelineDefinition)
    environment_dict = check.opt_dict_param(environment_dict, 'environment_dict')
    run_config = check_run_config_param(run_config)

    return PipelineExecutionResult(
        pipeline,
        run_config.run_id,
        list(
            execute_pipeline_iterator(
                pipeline=pipeline, environment_dict=environment_dict, run_config=run_config
            )
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
    if isinstance(pipeline_context.executor_config, InProcessExecutorConfig):
        step_events_gen = start_inprocess_executor(
            pipeline_context,
            execution_plan,
            pipeline_context.intermediates_manager,
            step_keys_to_execute,
        )
    elif isinstance(pipeline_context.executor_config, MultiprocessExecutorConfig):
        check.invariant(not step_keys_to_execute, 'subplan not supported for multiprocess yet')
        step_events_gen = multiprocess_execute_plan(pipeline_context, execution_plan)
    else:
        check.failed('Unsupported config {}'.format(pipeline_context.executor_config))

    for step_event in step_events_gen:
        yield step_event


def execute_plan(execution_plan, environment_dict=None, run_config=None):
    check.inst_param(execution_plan, 'execution_plan', ExecutionPlan)
    environment_dict = check.opt_dict_param(environment_dict, 'environment_dict')
    run_config = check_run_config_param(run_config)

    with yield_pipeline_execution_context(
        execution_plan.pipeline_def, environment_dict, run_config
    ) as pipeline_context:
        return list(invoke_executor_on_plan(pipeline_context, execution_plan))


def create_environment_config(pipeline, environment_dict=None):
    check.inst_param(pipeline, 'pipeline', PipelineDefinition)
    check.opt_dict_param(environment_dict, 'environment')

    result = evaluate_config_value(pipeline.environment_type, environment_dict)

    if not result.success:
        raise PipelineConfigEvaluationError(pipeline, result.errors, environment_dict)

    return construct_environment_config(result.value)


class ExecutionSelector(object):
    def __init__(self, name, solid_subset=None):
        self.name = check.str_param(name, 'name')
        if solid_subset is None:
            self.solid_subset = None
        else:
            self.solid_subset = check.opt_list_param(solid_subset, 'solid_subset', of_type=str)
