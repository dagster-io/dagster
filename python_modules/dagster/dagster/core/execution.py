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

from collections import defaultdict
from contextlib import contextmanager
import inspect
import itertools

from contextlib2 import ExitStack
from dagster import check
from dagster.utils import merge_dicts

from .definitions import (
    DependencyDefinition,
    PipelineDefinition,
    Solid,
    SolidInstance,
    solids_in_topological_order,
)

from .definitions.utils import DEFAULT_OUTPUT
from .definitions.environment_configs import construct_environment_config

from .execution_context import (
    ExecutionContext,
    ExecutionMetadata,
    PipelineExecutionContextData,
    PipelineExecutionContext,
)

from .errors import (
    DagsterInvariantViolationError,
    DagsterUnmarshalInputNotFoundError,
    DagsterMarshalOutputNotFoundError,
    DagsterExecutionStepNotFoundError,
)

from .events import construct_event_logger

from .execution_plan.create import (
    ExecutionPlanAddedOutputs,
    ExecutionPlanSubsetInfo,
    create_execution_plan_core,
)

from .execution_plan.objects import (
    ExecutionPlan,
    ExecutionStepEvent,
    ExecutionStepEventType,
    StepKind,
)

from .execution_plan.plan_subset import MarshalledOutput

from .execution_plan.simple_engine import iterate_step_events_for_execution_plan

from .init_context import InitContext, InitResourceContext

from .log import DagsterLog

from .system_config.objects import EnvironmentConfig

from .types.evaluator import EvaluationError, evaluate_config_value, friendly_string_for_error
from .types.marshal import FilePersistencePolicy


class PipelineExecutionResult(object):
    '''Result of execution of the whole pipeline. Returned eg by :py:func:`execute_pipeline`.

    Attributes:
        pipeline (PipelineDefinition): Pipeline that was executed
        context (ExecutionContext): ExecutionContext of that particular Pipeline run.
        result_list (list[SolidExecutionResult]): List of results for each pipeline solid.
    '''

    def __init__(self, pipeline, context, result_list):
        self.pipeline = check.inst_param(pipeline, 'pipeline', PipelineDefinition)
        self.context = check.inst_param(context, 'context', PipelineExecutionContext)
        self.result_list = check.list_param(
            result_list, 'result_list', of_type=SolidExecutionResult
        )
        self.run_id = context.run_id

    @property
    def success(self):
        '''Whether the pipeline execution was successful at all steps'''
        return all([result.success for result in self.result_list])

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

        for result in self.result_list:
            if result.solid.name == name:
                return result

        raise DagsterInvariantViolationError(
            'Did not find result for solid {name} in pipeline execution result'.format(name=name)
        )


class SolidExecutionResult(object):
    '''Execution result for one solid of the pipeline.

    Attributes:
      context (ExecutionContext): ExecutionContext of that particular Pipeline run.
      solid (SolidDefinition): Solid for which this result is
    '''

    def __init__(self, pipeline_context, solid, step_events_by_kind):
        self.context = check.inst_param(
            pipeline_context, 'pipeline_context', PipelineExecutionContext
        )
        self.solid = check.inst_param(solid, 'solid', Solid)
        self.step_events_by_kind = check.dict_param(
            step_events_by_kind, 'step_events_by_kind', key_type=StepKind, value_type=list
        )

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
        check.inst_param(pipeline_context, 'pipeline_context', PipelineExecutionContext)
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
                pipeline_context=pipeline_context,
                solid=step_events[0].step.solid,
                step_events_by_kind=dict(step_events_by_kind),
            )
        else:
            check.failed("Cannot create SolidExecutionResult from empty list")

    @property
    def success(self):
        '''Whether the solid execution was successful'''
        return all(
            [
                step_event.event_type == ExecutionStepEventType.STEP_OUTPUT
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
                result.success_data.output_name: result.success_data.value
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
                if result.success_data.output_name == output_name:
                    return result.success_data.value
            raise DagsterInvariantViolationError(
                (
                    'Did not find result {output_name} in solid {self.solid.name} '
                    'execution result'
                ).format(output_name=output_name, self=self)
            )
        else:
            return None

    @property
    def dagster_error(self):
        '''Returns exception that happened during this solid's execution, if any'''
        for result in itertools.chain(
            self.input_expectations, self.output_expectations, self.transforms
        ):
            if result.event_type == ExecutionStepEventType.STEP_FAILURE:
                return result.failure_data.dagster_error


def check_execution_metadata_param(execution_metadata):
    return (
        check.inst_param(execution_metadata, 'execution_metadata', ExecutionMetadata)
        if execution_metadata
        else ExecutionMetadata()
    )


def create_execution_plan(
    pipeline, environment_dict=None, execution_metadata=None, subset_info=None
):
    check.inst_param(pipeline, 'pipeline', PipelineDefinition)
    environment_dict = check.opt_dict_param(environment_dict, 'environment_dict', key_type=str)
    execution_metadata = check_execution_metadata_param(execution_metadata)
    check.inst_param(execution_metadata, 'execution_metadata', ExecutionMetadata)
    check.opt_inst_param(subset_info, 'subset_info', ExecutionPlanSubsetInfo)

    with yield_pipeline_execution_context(
        pipeline, environment_dict, execution_metadata
    ) as pipeline_context:
        return create_execution_plan_core(pipeline_context, execution_metadata, subset_info)


def get_tags(user_context_params, execution_metadata, pipeline):
    check.inst_param(user_context_params, 'user_context_params', ExecutionContext)
    check.opt_inst_param(execution_metadata, 'execution_metadata', ExecutionMetadata)
    check.inst_param(pipeline, 'pipeline', PipelineDefinition)

    base_tags = merge_dicts({'pipeline': pipeline.name}, user_context_params.tags)

    if execution_metadata and execution_metadata.tags:
        user_keys = set(user_context_params.tags.keys())
        provided_keys = set(execution_metadata.tags.keys())
        if not user_keys.isdisjoint(provided_keys):
            raise DagsterInvariantViolationError(
                (
                    'You have specified tags and user-defined tags '
                    'that overlap. User keys: {user_keys}. Reentrant keys: '
                    '{provided_keys}.'
                ).format(user_keys=user_keys, provided_keys=provided_keys)
            )

        return merge_dicts(base_tags, execution_metadata.tags)
    else:
        return base_tags


def _ensure_gen(thing_or_gen):
    if not inspect.isgenerator(thing_or_gen):

        def _gen_thing():
            yield thing_or_gen

        return _gen_thing()

    return thing_or_gen


@contextmanager
def with_maybe_gen(thing_or_gen):
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


@contextmanager
def yield_pipeline_execution_context(pipeline_def, environment_dict, execution_metadata):
    check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition)
    check.dict_param(environment_dict, 'environment_dict', key_type=str)
    check.inst_param(execution_metadata, 'execution_metadata', ExecutionMetadata)

    environment_config = create_environment_config(pipeline_def, environment_dict)

    context_definition = pipeline_def.context_definitions[environment_config.context.name]

    ec_or_gen = context_definition.context_fn(
        InitContext(
            context_config=environment_config.context.config,
            pipeline_def=pipeline_def,
            run_id=execution_metadata.run_id,
        )
    )

    with with_maybe_gen(ec_or_gen) as execution_context:
        check.inst(execution_context, ExecutionContext)

        with _create_resources(
            pipeline_def,
            context_definition,
            environment_config,
            execution_context,
            execution_metadata.run_id,
        ) as resources:
            yield construct_pipeline_execution_context(
                execution_metadata, execution_context, pipeline_def, resources, environment_config
            )


def construct_pipeline_execution_context(
    execution_metadata, execution_context, pipeline, resources, environment_config
):
    check.inst_param(execution_metadata, 'execution_metadata', ExecutionMetadata)
    check.inst_param(execution_context, 'execution_context', ExecutionContext)
    check.inst_param(pipeline, 'pipeline', PipelineDefinition)
    check.inst_param(environment_config, 'environment_config', EnvironmentConfig)

    loggers = _create_loggers(execution_metadata, execution_context)
    tags = get_tags(execution_context, execution_metadata, pipeline)
    log = DagsterLog(execution_metadata.run_id, tags, loggers)

    return PipelineExecutionContext(
        PipelineExecutionContextData(
            pipeline_def=pipeline,
            run_id=execution_metadata.run_id,
            resources=resources,
            event_callback=execution_metadata.event_callback,
            environment_config=environment_config,
            persistence_strategy=_create_persistence_strategy(
                environment_config.context.persistence
            ),
        ),
        tags=tags,
        log=log,
    )


def _create_loggers(execution_metadata, execution_context):
    check.inst_param(execution_metadata, 'execution_metadata', ExecutionMetadata)
    check.inst_param(execution_context, 'execution_context', ExecutionContext)

    if execution_metadata.event_callback:
        return execution_context.loggers + [
            construct_event_logger(execution_metadata.event_callback)
        ]
    elif execution_metadata.loggers:
        return execution_context.loggers + execution_metadata.loggers
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

            resource_obj = stack.enter_context(with_maybe_gen(resource_obj_or_gen))

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


def _do_iterate_pipeline(pipeline, pipeline_context, execution_metadata, throw_on_user_error=True):
    check.inst_param(pipeline, 'pipeline', PipelineDefinition)
    check.inst_param(pipeline_context, 'context', PipelineExecutionContext)
    check.inst_param(execution_metadata, 'execution_metadata', ExecutionMetadata)
    check.bool_param(throw_on_user_error, 'throw_on_user_error')

    pipeline_context.events.pipeline_start()

    execution_plan = create_execution_plan_core(pipeline_context, execution_metadata)

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

    for solid_result in _process_step_events(
        pipeline_context,
        pipeline,
        iterate_step_events_for_execution_plan(
            pipeline_context, execution_plan, throw_on_user_error
        ),
    ):
        if not solid_result.success:
            pipeline_success = False
        yield solid_result

    if pipeline_success:
        pipeline_context.events.pipeline_success()
    else:
        pipeline_context.events.pipeline_failure()


def execute_pipeline_iterator(
    pipeline,
    environment_dict=None,
    throw_on_user_error=True,
    execution_metadata=None,
    solid_subset=None,
):
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
    check.bool_param(throw_on_user_error, 'throw_on_user_error')
    execution_metadata = check_execution_metadata_param(execution_metadata)
    check.opt_list_param(solid_subset, 'solid_subset', of_type=str)

    pipeline_to_execute = get_subset_pipeline(pipeline, solid_subset)
    with yield_pipeline_execution_context(
        pipeline_to_execute, environment_dict, execution_metadata
    ) as pipeline_context:
        for solid_result in _do_iterate_pipeline(
            pipeline_to_execute,
            pipeline_context,
            execution_metadata=execution_metadata,
            throw_on_user_error=throw_on_user_error,
        ):
            yield solid_result


def _process_step_events(pipeline_context, pipeline, step_events):
    check.inst_param(pipeline_context, 'pipeline_context', PipelineExecutionContext)
    check.inst_param(pipeline, 'pipeline', PipelineDefinition)

    # TODO: actually make this stream results. Right now it collects
    # all results that then constructs solid result
    # see https://github.com/dagster-io/dagster/issues/792
    step_events = check.list_param(list(step_events), 'step_events', of_type=ExecutionStepEvent)

    step_events_by_solid_name = defaultdict(list)
    for step_event in step_events:
        check.inst(step_event, ExecutionStepEvent)
        step_events_by_solid_name[step_event.step.solid.name].append(step_event)

    for solid in solids_in_topological_order(pipeline):
        if solid.name in step_events_by_solid_name:
            yield SolidExecutionResult.from_step_events(
                pipeline_context, step_events_by_solid_name[solid.name]
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


def execute_externalized_plan(
    pipeline,
    execution_plan,
    step_keys,
    inputs_to_marshal=None,
    outputs_to_marshal=None,
    environment_dict=None,
    execution_metadata=None,
    throw_on_user_error=True,
):
    check.inst_param(pipeline, 'pipeline', PipelineDefinition)
    check.inst_param(execution_plan, 'execution_plan', ExecutionPlan)
    check.list_param(step_keys, 'step_keys', of_type=str)
    inputs_to_marshal = check.opt_two_dim_dict_param(
        inputs_to_marshal, 'inputs_to_marshal', value_type=str
    )
    outputs_to_marshal = check.opt_dict_param(
        outputs_to_marshal, 'outputs_to_marshal', key_type=str, value_type=list
    )
    for output_list in outputs_to_marshal.values():
        check.list_param(output_list, 'outputs_to_marshal', of_type=MarshalledOutput)

    environment_dict = check.opt_dict_param(environment_dict, 'environment_dict')
    execution_metadata = check_execution_metadata_param(execution_metadata)

    _check_inputs_to_marshal(execution_plan, inputs_to_marshal)
    _check_outputs_to_marshal(execution_plan, outputs_to_marshal)

    with yield_pipeline_execution_context(
        pipeline, environment_dict, execution_metadata
    ) as pipeline_context:

        execution_plan = create_execution_plan_core(
            pipeline_context,
            execution_metadata=execution_metadata,
            subset_info=ExecutionPlanSubsetInfo.with_input_marshalling(
                included_step_keys=step_keys, marshalled_inputs=inputs_to_marshal
            ),
            added_outputs=ExecutionPlanAddedOutputs.with_output_marshalling(outputs_to_marshal),
        )

        return list(
            iterate_step_events_for_execution_plan(
                pipeline_context, execution_plan, throw_on_user_error=throw_on_user_error
            )
        )


def _check_outputs_to_marshal(execution_plan, outputs_to_marshal):
    if not outputs_to_marshal:
        return

    for step_key, outputs_for_step in outputs_to_marshal.items():
        if not execution_plan.has_step(step_key):
            raise DagsterExecutionStepNotFoundError(step_key=step_key)
        step = execution_plan.get_step_by_key(step_key)
        for output in outputs_for_step:
            output_name = output.output_name
            if not step.has_step_output(output_name):
                raise DagsterMarshalOutputNotFoundError(
                    'Execution step {step_key} does not have output {output}'.format(
                        step_key=step_key, output=output_name
                    ),
                    step_key=step_key,
                    output_name=output_name,
                )


def _check_inputs_to_marshal(execution_plan, inputs_to_marshal):
    if not inputs_to_marshal:
        return

    for step_key, input_dict in inputs_to_marshal.items():
        if not execution_plan.has_step(step_key):
            raise DagsterExecutionStepNotFoundError(step_key=step_key)
        step = execution_plan.get_step_by_key(step_key)
        for input_name in input_dict.keys():
            if input_name not in step.step_input_dict:
                raise DagsterUnmarshalInputNotFoundError(
                    'Input {input_name} does not exist in execution step {key}'.format(
                        input_name=input_name, key=step.key
                    ),
                    input_name=input_name,
                    step_key=step.key,
                )


def execute_plan(
    pipeline,
    execution_plan,
    environment_dict=None,
    execution_metadata=None,
    throw_on_user_error=True,
):
    check.inst_param(pipeline, 'pipeline', PipelineDefinition)
    check.inst_param(execution_plan, 'execution_plan', ExecutionPlan)
    environment_dict = check.opt_dict_param(environment_dict, 'environment_dict')

    execution_metadata = check_execution_metadata_param(execution_metadata)

    with yield_pipeline_execution_context(
        pipeline, environment_dict, execution_metadata
    ) as pipeline_context:
        return list(
            iterate_step_events_for_execution_plan(
                pipeline_context, execution_plan, throw_on_user_error=throw_on_user_error
            )
        )


def execute_pipeline(
    pipeline,
    environment_dict=None,
    throw_on_user_error=True,
    execution_metadata=None,
    solid_subset=None,
):
    '''
    "Synchronous" version of :py:func:`execute_pipeline_iterator`.

    Note: throw_on_user_error is very useful in testing contexts when not testing for error conditions

    Parameters:
      pipeline (PipelineDefinition): Pipeline to run
      environment (dict): The enviroment that parameterizes this run
      throw_on_user_error (bool):
        throw_on_user_error makes the function throw when an error is encoutered rather than returning
        the py:class:`SolidExecutionResult` in an error-state.


    Returns:
      PipelineExecutionResult
    '''

    check.inst_param(pipeline, 'pipeline', PipelineDefinition)
    environment_dict = check.opt_dict_param(environment_dict, 'environment_dict')
    check.bool_param(throw_on_user_error, 'throw_on_user_error')
    execution_metadata = check_execution_metadata_param(execution_metadata)
    check.opt_list_param(solid_subset, 'solid_subset', of_type=str)

    pipeline_to_execute = get_subset_pipeline(pipeline, solid_subset)
    return execute_pipeline_with_metadata(
        pipeline_to_execute,
        environment_dict,
        execution_metadata=execution_metadata,
        throw_on_user_error=throw_on_user_error,
    )


def _dep_key_of(solid):
    return SolidInstance(solid.definition.name, solid.name)


def build_sub_pipeline(pipeline_def, solid_names):
    '''
    Build a pipeline which is a subset of another pipeline.
    Only includes the solids which are in solid_names.
    '''

    check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition)
    check.list_param(solid_names, 'solid_names', of_type=str)

    solid_name_set = set(solid_names)
    solids = list(map(pipeline_def.solid_named, solid_names))
    deps = {_dep_key_of(solid): {} for solid in solids}

    def _out_handle_of_inp(input_handle):
        if pipeline_def.dependency_structure.has_dep(input_handle):
            output_handle = pipeline_def.dependency_structure.get_dep(input_handle)
            if output_handle.solid.name in solid_name_set:
                return output_handle
        return None

    for solid in solids:
        for input_handle in solid.input_handles():
            output_handle = _out_handle_of_inp(input_handle)
            if output_handle:
                deps[_dep_key_of(solid)][input_handle.input_def.name] = DependencyDefinition(
                    solid=output_handle.solid.name, output=output_handle.output_def.name
                )

    return PipelineDefinition(
        name=pipeline_def.name,
        solids=list({solid.definition for solid in solids}),
        context_definitions=pipeline_def.context_definitions,
        dependencies=deps,
    )


def execute_pipeline_with_metadata(
    pipeline, environment_dict, execution_metadata, throw_on_user_error
):
    check.inst_param(pipeline, 'pipeline', PipelineDefinition)
    environment_dict = check.opt_dict_param(environment_dict, 'environment_dict')
    check.inst_param(execution_metadata, 'execution_metadata', ExecutionMetadata)

    with yield_pipeline_execution_context(
        pipeline, environment_dict, execution_metadata
    ) as pipeline_context:
        return PipelineExecutionResult(
            pipeline,
            pipeline_context,
            list(
                _do_iterate_pipeline(
                    pipeline,
                    pipeline_context,
                    execution_metadata=execution_metadata,
                    throw_on_user_error=throw_on_user_error,
                )
            ),
        )


def get_subset_pipeline(pipeline, solid_subset):
    check.inst_param(pipeline, 'pipeline', PipelineDefinition)
    check.opt_list_param(solid_subset, 'solid_subset', of_type=str)
    return pipeline if solid_subset is None else build_sub_pipeline(pipeline, solid_subset)


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
