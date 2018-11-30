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

from collections import namedtuple
from contextlib import contextmanager
import json
import itertools
import inspect
import uuid

import six

from dagster import (
    check,
    config,
)

from .definitions import (
    DEFAULT_OUTPUT,
    ContextCreationExecutionInfo,
    ExecutionGraph,
    PipelineDefinition,
    Solid,
)

from .config_types import EnvironmentConfigType

from .execution_context import (
    ExecutionContext,
    RuntimeExecutionContext,
)

from .errors import (
    DagsterInvariantViolationError,
    DagsterTypeError,
    DagsterUserCodeExecutionError,
)

from .evaluator import (
    DagsterEvaluateConfigValueError,
    evaluate_config_value,
    throwing_evaluate_config_value,
)

from .execution_plan import (
    ExecutionPlanInfo,
    StepResult,
    StepTag,
    create_execution_plan_core,
    execute_steps,
)


class PipelineExecutionResult(object):
    '''Result of execution of the whole pipeline. Returned eg by :py:function:`execute_pipeline`.

    Attributes:
        pipeline (PipelineDefinition): Pipeline that was executed
        context (ExecutionContext): ExecutionContext of that particular Pipeline run.
        result_list (list[SolidExecutionResult]): List of results for each pipeline solid.
    '''

    def __init__(
        self,
        pipeline,
        context,
        result_list,
    ):
        self.pipeline = check.inst_param(pipeline, 'pipeline', PipelineDefinition)
        self.context = check.inst_param(context, 'context', RuntimeExecutionContext)
        self.result_list = check.list_param(
            result_list,
            'result_list',
            of_type=SolidExecutionResult,
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
                    name=name,
                    pipeline=self.pipeline.display_name,
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

    def __init__(self, context, solid, input_expectations, transforms, output_expectations):
        self.context = check.inst_param(context, 'context', RuntimeExecutionContext)
        self.solid = check.inst_param(solid, 'solid', Solid)
        self.input_expectations = check.list_param(
            input_expectations,
            'input_expectations',
            StepResult,
        )
        self.output_expectations = check.list_param(
            output_expectations,
            'output_expectations',
            StepResult,
        )
        self.transforms = check.list_param(transforms, 'transforms', StepResult)

    @staticmethod
    def from_results(context, results):
        results = check.list_param(results, 'results', StepResult)
        if results:
            input_expectations = []
            output_expectations = []
            transforms = []

            for result in results:
                if result.tag == StepTag.INPUT_EXPECTATION:
                    input_expectations.append(result)
                elif result.tag == StepTag.OUTPUT_EXPECTATION:
                    output_expectations.append(result)
                elif result.tag == StepTag.TRANSFORM:
                    transforms.append(result)

            return SolidExecutionResult(
                context=context,
                solid=results[0].step.solid,
                input_expectations=input_expectations,
                output_expectations=output_expectations,
                transforms=transforms,
            )
        else:
            check.failed("Cannot create SolidExecutionResult from empty list")

    @property
    def success(self):
        '''Whether the solid execution was successful'''
        return all(
            [
                result.success for result in
                itertools.chain(self.input_expectations, self.output_expectations, self.transforms)
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
                    output_name=output_name,
                    solid=self.solid.name,
                )
            )

        if self.success:
            for result in self.transforms:
                if result.success_data.output_name == output_name:
                    return result.success_data.value
            raise DagsterInvariantViolationError(
                'Did not find result {output_name} in solid {self.solid.name} execution result'.
                format(output_name=output_name, self=self)
            )
        else:
            return None

    def reraise_user_error(self):
        if not self.success:
            for result in itertools.chain(
                self.input_expectations, self.output_expectations, self.transforms
            ):
                if not result.success:
                    if isinstance(
                        result.failure_data.dagster_error,
                        DagsterUserCodeExecutionError,
                    ):
                        six.reraise(*result.failure_data.dagster_error.original_exc_info)
                    else:
                        raise result.failure_data.dagster_error

    @property
    def dagster_error(self):
        '''Returns exception that happened during this solid's execution, if any'''
        for result in itertools.chain(
            self.input_expectations, self.output_expectations, self.transforms
        ):
            if not result.success:
                return result.failure_data.dagster_error


def _wrap_in_yield(context_params_or_gen):
    check.param_invariant(
        inspect.isgenerator(context_params_or_gen)
        or isinstance(context_params_or_gen, ExecutionContext),
        'context_params_or_gen',
    )

    if isinstance(context_params_or_gen, ExecutionContext):

        def _gen_for_context_params():
            yield context_params_or_gen

        return _gen_for_context_params()

    return context_params_or_gen


def _validate_environment(environment, pipeline):
    context_name = environment.context.name

    if context_name not in pipeline.context_definitions:
        avaiable_context_keys = list(pipeline.context_definitions.keys())
        raise DagsterInvariantViolationError(
            'Context {context_name} not found in '.format(context_name=context_name) + \
            'pipeline definiton. Available contexts {avaiable_context_keys}'.format(
                avaiable_context_keys=repr(avaiable_context_keys),
            )
        )

    for solid_name in environment.solids.keys():
        if not pipeline.has_solid(solid_name):
            available_solids = [s.name for s in pipeline.solids]
            raise DagsterInvariantViolationError(
                'Solid {solid_name} specified in config for pipeline {pipeline} not found.'.format(
                    solid_name=solid_name,
                    pipeline=pipeline.display_name,
                ) + \
                ' Available solids in pipeline are {solids}.'.format(solids=available_solids)
            )


def create_execution_plan(pipeline, environment=None):
    check.inst_param(pipeline, 'pipeline', PipelineDefinition)
    check.opt_inst_param(environment, 'environment', config.Environment)

    pipeline_env_type = pipeline.environment_type

    if environment is None:
        environment = evaluate_config_value(pipeline_env_type, None).value

    check.inst(environment, config.Environment)

    execution_graph = ExecutionGraph.from_pipeline(pipeline)
    with yield_context(pipeline, environment) as context:
        return create_execution_plan_core(
            ExecutionPlanInfo(context, execution_graph, environment),
        )


def create_config_value(config_type, config_input):
    if isinstance(config_input, config.Environment):
        return config_input

    try:
        # TODO: we should bubble up multiple errors from here
        return throwing_evaluate_config_value(config_type, config_input)
    except DagsterEvaluateConfigValueError as e:
        raise DagsterTypeError(
            'Invalid config value on type {dagster_type}: {error_msg}. Value received {value}'.
            format(
                value=json.dumps(config_input, indent=2)
                if isinstance(config_input, dict) else config_input,
                dagster_type=config_type.name,
                error_msg=','.join(e.args),
            )
        )


def get_run_id(reentrant_info):
    check.opt_inst_param(reentrant_info, 'reentrant_info', ReentrantInfo)
    if reentrant_info and reentrant_info.run_id:
        return reentrant_info.run_id
    else:
        return str(uuid.uuid4())


def merge_two_dicts(left, right):
    result = left.copy()
    result.update(right)
    return result


def get_context_stack(user_context_params, reentrant_info):
    check.inst(user_context_params, ExecutionContext)
    check.opt_inst_param(reentrant_info, 'reentrant_info', ReentrantInfo)

    if reentrant_info and reentrant_info.context_stack:
        user_keys = set(user_context_params.context_stack.keys())
        reentrant_keys = set(reentrant_info.context_stack.keys())
        if not user_keys.isdisjoint(reentrant_keys):
            raise DagsterInvariantViolationError(
                (
                    'You have specified re-entrant keys and user-defined keys '
                    'that overlap. User keys: {user_keys}. Reentrant keys: '
                    '{reentrant_keys}.'
                ).format(
                    user_keys=user_keys,
                    reentrant_keys=reentrant_keys,
                )
            )

        return merge_two_dicts(user_context_params.context_stack, reentrant_info.context_stack)
    else:
        return user_context_params.context_stack


@contextmanager
def yield_context(pipeline, environment, reentrant_info=None):
    check.inst_param(pipeline, 'pipeline', PipelineDefinition)
    check.inst_param(environment, 'environment', config.Environment)
    check.opt_inst_param(reentrant_info, 'reentrant_info', ReentrantInfo)

    _validate_environment(environment, pipeline)

    context_name = environment.context.name
    context_definition = pipeline.context_definitions[context_name]
    config_type = context_definition.config_field.dagster_type

    config_value = create_config_value(config_type, environment.context.config)

    context_params_or_gen = context_definition.context_fn(
        ContextCreationExecutionInfo(
            config=config_value,
            pipeline_def=pipeline,
        )
    )

    called = False

    for user_context_params in _wrap_in_yield(context_params_or_gen):
        check.invariant(not called, 'should only yield one thing')
        check.inst(user_context_params, ExecutionContext)

        run_id = get_run_id(reentrant_info)
        context_stack = get_context_stack(user_context_params, reentrant_info)

        runtime_context = RuntimeExecutionContext(
            run_id=run_id,
            loggers=user_context_params.loggers,
            resources=user_context_params.resources,
            context_stack=context_stack,
        )
        yield runtime_context

        called = True


def execute_pipeline_iterator(pipeline, environment):
    '''Returns iterator that yields :py:class:`SolidExecutionResult` for each
    solid executed in the pipeline.

    This is intended to allow the caller to do things between each executed
    node. For the 'synchronous' API, see :py:function:`execute_pipeline`.

    Parameters:
      pipeline (PipelineDefinition): pipeline to run
      execution (ExecutionContext): execution context of the run
    '''
    check.inst_param(pipeline, 'pipeline', PipelineDefinition)

    pipeline_env_type = EnvironmentConfigType(pipeline)

    environment = create_config_value(pipeline_env_type, environment)

    check.inst_param(environment, 'environment', config.Environment)

    execution_graph = ExecutionGraph.from_pipeline(pipeline)
    with yield_context(pipeline, environment) as context:
        with context.value('pipeline', execution_graph.pipeline.display_name):
            for result in _execute_graph_iterator(context, execution_graph, environment):
                yield result


def _execute_graph_iterator(context, execution_graph, environment):
    check.inst_param(context, 'context', RuntimeExecutionContext)
    check.inst_param(execution_graph, 'execution_graph', ExecutionGraph)
    check.inst_param(environment, 'environent', config.Environment)

    execution_plan = create_execution_plan_core(
        ExecutionPlanInfo(
            context,
            execution_graph,
            environment,
        ),
    )

    steps = list(execution_plan.topological_steps())

    if not steps:
        context.debug(
            'Pipeline {pipeline} has no nodes and no execution will happen'.format(
                pipeline=execution_graph.pipeline.display_name
            )
        )
        return

    context.debug(
        'About to execute the compute node graph in the following order {order}'.format(
            order=[step.key for step in steps]
        )
    )

    check.invariant(len(steps[0].step_inputs) == 0)

    solid = None
    solid_results = []
    for step_result in execute_steps(context, steps):
        step = step_result.step

        if solid and solid is not step.solid:
            yield SolidExecutionResult.from_results(context, solid_results)
            solid_results = []

        if not step_result.success:
            solid_results.append(step_result)
            yield SolidExecutionResult.from_results(context, solid_results)
            solid_results = []
            return

        solid = step.solid
        solid_results.append(step_result)

    if solid and solid_results:
        yield SolidExecutionResult.from_results(context, solid_results)


def get_key_or_prop(obj, key):
    check.str_param(key, 'key')

    if isinstance(obj, dict):
        return obj.get(key)
    else:
        if not hasattr(obj, key):
            return None
        return getattr(obj, key, None)


def check_environment(pipeline, environment):
    check.inst_param(pipeline, 'pipeline', PipelineDefinition)
    check.opt_inst_param(environment, 'environment', (config.Environment, dict))

    if not environment:
        return

    solids_in_config = get_key_or_prop(environment, 'solids')

    if solids_in_config:
        for solid_name in solids_in_config:
            if not pipeline.has_solid(solid_name):
                raise DagsterTypeError(
                    (
                        'Solid {solid_name} does not exist on pipeline {pipeline_name}. '
                        'You passed in {solid_name} to the solids field of the environment.'
                    ).format(
                        solid_name=solid_name,
                        pipeline_name=pipeline.name,
                    )
                )

    context_in_config = get_key_or_prop(environment, 'context')

    if context_in_config:
        if isinstance(context_in_config, config.Context):
            context_name = context_in_config.name
        elif isinstance(context_in_config, dict):
            if len(context_in_config) > 1:
                raise DagsterTypeError('Cannot specify more than one context')

            context_name = list(context_in_config.keys())[0]
        else:
            check.failed('invalid object')

        if not pipeline.has_context(context_name):
            raise DagsterTypeError(
                (
                    'Context {context_name} does not exist on pipeline {pipeline_name}. '
                    'You passed in {context_name} to the context field of the Environment.'
                ).format(
                    context_name=context_name,
                    pipeline_name=pipeline.name,
                )
            )


class ReentrantInfo(namedtuple('_ReentrantInfo', 'run_id context_stack')):
    def __new__(cls, run_id=None, context_stack=None):
        return super(ReentrantInfo, cls).__new__(
            cls,
            run_id=check.opt_str_param(run_id, 'run_id'),
            context_stack=check.opt_dict_param(context_stack, 'context_stack'),
        )


def execute_pipeline(
    pipeline,
    environment=None,
    throw_on_error=True,
    reentrant_info=None,
):
    '''
    "Synchronous" version of :py:function:`execute_pipeline_iterator`.

    Note: throw_on_error is very useful in testing contexts when not testing for error conditions

    Parameters:
      pipeline (PipelineDefinition): Pipeline to run
      environment (config.Environment | dict): The enviroment that parameterizes this run
      throw_on_error (bool):
        throw_on_error makes the function throw when an error is encoutered rather than returning
        the py:class:`SolidExecutionResult` in an error-state.


    Returns:
      PipelineExecutionResult
    '''

    check.inst_param(pipeline, 'pipeline', PipelineDefinition)
    check.opt_inst_param(environment, 'environment', (dict, config.Environment))
    check.bool_param(throw_on_error, 'throw_on_error')
    check.opt_inst_param(reentrant_info, 'reentrant_info', ReentrantInfo)

    check_environment(pipeline, environment)

    pipeline_env_type = pipeline.environment_type
    environment = create_config_value(pipeline_env_type, environment)

    execution_graph = ExecutionGraph.from_pipeline(pipeline)
    return _execute_graph(execution_graph, environment, throw_on_error, reentrant_info)


def _execute_graph(
    execution_graph,
    environment,
    throw_on_error=True,
    reentrant_info=None,
):
    check.inst_param(execution_graph, 'execution_graph', ExecutionGraph)
    check.inst_param(environment, 'environment', config.Environment)
    check.bool_param(throw_on_error, 'throw_on_error')
    check.opt_inst_param(reentrant_info, 'reentrant_info', ReentrantInfo)

    results = []
    with yield_context(execution_graph.pipeline, environment, reentrant_info) as context:
        check.inst(context, RuntimeExecutionContext)
        with context.value('pipeline', execution_graph.pipeline.display_name):
            context.events.pipeline_start()

            for result in _execute_graph_iterator(context, execution_graph, environment):
                if throw_on_error and not result.success:
                    result.reraise_user_error()

                results.append(result)

            pipeline_result = PipelineExecutionResult(execution_graph.pipeline, context, results)
            if pipeline_result.success:
                context.events.pipeline_success()
            else:
                context.events.pipeline_failure()

            return pipeline_result
