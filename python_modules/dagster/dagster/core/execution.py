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
    EvaluationError,
    evaluate_config_value,
    friendly_string_for_error,
    throwing_evaluate_config_value,
)

from .events import construct_event_logger

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


def create_runtime_context(execution_context, reentrant_info):
    check.inst_param(execution_context, 'execution_context', ExecutionContext)
    check.opt_inst_param(reentrant_info, 'reentrant_info', ReentrantInfo)

    run_id = get_run_id(reentrant_info)
    context_stack = get_context_stack(execution_context, reentrant_info)

    if reentrant_info and reentrant_info.event_callback:
        loggers = execution_context.loggers + [
            construct_event_logger(reentrant_info.event_callback)
        ]
    else:
        loggers = execution_context.loggers

    return RuntimeExecutionContext(
        run_id=run_id,
        loggers=loggers,
        resources=execution_context.resources,
        context_stack=context_stack,
    )


@contextmanager
def yield_context(pipeline, environment, reentrant_info=None):
    check.inst_param(pipeline, 'pipeline', PipelineDefinition)
    check.inst_param(environment, 'environment', config.Environment)
    check.opt_inst_param(reentrant_info, 'reentrant_info', ReentrantInfo)

    context_definition = pipeline.context_definitions[environment.context.name]

    run_id = get_run_id(reentrant_info)

    ec_or_gen = context_definition.context_fn(
        ContextCreationExecutionInfo(
            config=environment.context.config,
            pipeline_def=pipeline,
            run_id=run_id,
        ),
    )

    called = False

    for execution_context in _wrap_in_yield(ec_or_gen):
        check.invariant(not called, 'should only yield one thing')
        check.inst(execution_context, ExecutionContext)

        yield create_runtime_context(execution_context, reentrant_info)

        called = True


def execute_pipeline_iterator(pipeline, environment=None):
    '''Returns iterator that yields :py:class:`SolidExecutionResult` for each
    solid executed in the pipeline.

    This is intended to allow the caller to do things between each executed
    node. For the 'synchronous' API, see :py:function:`execute_pipeline`.

    Parameters:
      pipeline (PipelineDefinition): pipeline to run
      execution (ExecutionContext): execution context of the run
    '''
    check.inst_param(pipeline, 'pipeline', PipelineDefinition)

    typed_environment = get_typed_environment(pipeline, environment)

    execution_graph = ExecutionGraph.from_pipeline(pipeline)
    with yield_context(pipeline, typed_environment) as context:
        with context.value('pipeline', execution_graph.pipeline.display_name):
            for result in _execute_graph_iterator(context, execution_graph, typed_environment):
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


class ReentrantInfo(namedtuple('_ReentrantInfo', 'run_id context_stack event_callback')):
    def __new__(cls, run_id=None, context_stack=None, event_callback=None):
        return super(ReentrantInfo, cls).__new__(
            cls,
            run_id=check.opt_str_param(run_id, 'run_id'),
            context_stack=check.opt_dict_param(context_stack, 'context_stack'),
            event_callback=check.opt_callable_param(event_callback, 'event_callback'),
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
                i_error=i_error + 1,
                error_message=error_message,
            )

        self.message = error_msg
        self.error_messages = error_messages

        super(PipelineConfigEvaluationError, self).__init__(error_msg, *args, **kwargs)


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
    check.opt_dict_param(environment, 'environment')
    check.bool_param(throw_on_error, 'throw_on_error')
    check.opt_inst_param(reentrant_info, 'reentrant_info', ReentrantInfo)

    typed_environment = get_typed_environment(pipeline, environment)

    return execute_reentrant_pipeline(pipeline, typed_environment, reentrant_info)


def execute_reentrant_pipeline(pipeline, typed_environment, reentrant_info):
    check.inst_param(pipeline, 'pipeline', PipelineDefinition)
    check.inst_param(typed_environment, 'typed_environment', config.Environment)
    check.opt_inst_param(reentrant_info, 'reentrant_info', ReentrantInfo)

    execution_graph = ExecutionGraph.from_pipeline(pipeline)
    return _execute_graph(
        execution_graph,
        typed_environment,
        throw_on_error=False,
        reentrant_info=reentrant_info,
    )


def get_typed_environment(pipeline, environment):
    check.inst_param(pipeline, 'pipeline', PipelineDefinition)
    check.opt_dict_param(environment, 'environment')

    pipeline_env_type = pipeline.environment_type
    result = evaluate_config_value(pipeline_env_type, environment)

    if not result.success:
        raise PipelineConfigEvaluationError(pipeline, result.errors, environment)

    return result.value


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
