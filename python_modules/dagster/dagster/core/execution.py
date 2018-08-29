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

from contextlib import contextmanager
import itertools
import copy

import six

from dagster import (
    check,
    config,
)

from .definitions import (
    SolidDefinition, PipelineDefinition, PipelineContextDefinition, DEFAULT_OUTPUT
)

from .errors import (
    DagsterUserCodeExecutionError,
    DagsterInvariantViolationError,
)

from .argument_handling import validate_args

from .compute_nodes import (
    ComputeNodeTag,
    ComputeNodeResult,
    create_compute_node_graph_from_env,
    execute_compute_nodes,
)

from .execution_context import ExecutionContext

from .graph import ExecutionGraph


class PipelineExecutionResult:
    def __init__(
        self,
        context,
        result_list,
    ):
        self.context = check.inst_param(context, 'context', ExecutionContext)
        self.result_list = check.list_param(
            result_list, 'result_list', of_type=SolidExecutionResult
        )

    @property
    def success(self):
        return all([result.success for result in self.result_list])

    def result_for_solid(self, name):
        check.str_param(name, 'name')
        for result in self.result_list:
            if result.solid.name == name:
                return result
        check.failed(
            'Did not find result for solid {name} in pipeline execution result'.format(name=name)
        )


class SolidExecutionResult:
    def __init__(self, *, context, solid, input_expectations, transforms, output_expectations):
        self.context = check.inst_param(context, 'context', ExecutionContext)
        self.solid = check.inst_param(solid, 'solid', SolidDefinition)
        self.input_expectations = check.list_param(
            input_expectations, 'input_expectations', ComputeNodeResult
        )
        self.output_expectations = check.list_param(
            output_expectations, 'output_expectations', ComputeNodeResult
        )
        self.transforms = check.list_param(transforms, 'transforms', ComputeNodeResult)

    @staticmethod
    def from_results(context, results):
        results = check.list_param(results, 'results', ComputeNodeResult)
        if results:
            input_expectations = []
            output_expectations = []
            transforms = []

            for result in results:
                if result.tag == ComputeNodeTag.INPUT_EXPECTATION:
                    input_expectations.append(result)
                elif result.tag == ComputeNodeTag.OUTPUT_EXPECTATION:
                    output_expectations.append(result)
                elif result.tag == ComputeNodeTag.TRANSFORM:
                    transforms.append(result)

            return SolidExecutionResult(
                context=context,
                solid=results[0].compute_node.solid,
                input_expectations=input_expectations,
                output_expectations=output_expectations,
                transforms=transforms,
            )
        else:
            check.failed("Cannot create SolidExecutionResult from empty list")

    @property
    def success(self):
        return all(
            [
                result.success for result in
                itertools.chain(self.input_expectations, self.output_expectations, self.transforms)
            ]
        )

    @property
    def transformed_values(self):
        if self.success and self.transforms:
            return {
                result.success_data.output_name: result.success_data.value
                for result in self.transforms
            }
        else:
            return None

    def transformed_value(self, output_name=DEFAULT_OUTPUT):
        check.str_param(output_name, 'output_name')
        if self.success:
            for result in self.transforms:
                if result.success_data.output_name == output_name:
                    return result.success_data.value
            check.failed(
                f'Did not find result {output_name} in solid {self.solid.name} execution result'
            )
        else:
            return None

    def reraise_user_error(self):
        if not self.success:
            for result in itertools.chain(
                self.input_expectations, self.output_expectations, self.transforms
            ):
                if not result.success:
                    six.reraise(*result.failure_data.dagster_user_exception.original_exc_info)

    @property
    def dagster_user_exception(self):
        for result in itertools.chain(
            self.input_expectations, self.output_expectations, self.transforms
        ):
            if not result.success:
                return result.failure_data.dagster_user_exception


def _do_throw_on_error(execution_result):
    check.inst_param(execution_result, 'execution_result', SolidExecutionResult)
    if execution_result.success:
        return
    else:
        execution_result.reraise_user_error()


def _wrap_in_yield(thing):
    if isinstance(thing, ExecutionContext):

        def _wrap():
            yield thing

        return _wrap()

    return thing


def _validate_environment(environment, pipeline):
    context_name = environment.context.name

    if context_name not in pipeline.context_definitions:
        avaiable_context_keys = list(pipeline.context_definitions.keys())
        raise DagsterInvariantViolationError(f'Context {context_name} not found in ' + \
            f'pipeline definiton. Available contexts {repr(avaiable_context_keys)}'
        )


class DagsterEnv:
    def __init__(self, execution_graph, environment):
        # This is not necessarily the best spot for these calls
        pipeline = execution_graph.pipeline
        _validate_environment(environment, pipeline)
        self.pipeline = check.inst_param(pipeline, 'pipeline', PipelineDefinition)
        self.environment = check.inst_param(environment, 'environment', config.Environment)

    @contextmanager
    def yield_context(self):
        context_name = self.environment.context.name
        context_definition = self.pipeline.context_definitions[context_name]

        args_to_pass = validate_args(
            self.pipeline.context_definitions[context_name].argument_def_dict,
            self.environment.context.args, 'pipeline {pipeline_name} context {context_name}'.format(
                pipeline_name=self.pipeline.name,
                context_name=context_name,
            )
        )

        thing = context_definition.context_fn(self.pipeline, args_to_pass)
        return _wrap_in_yield(thing)

    @property
    def evaluate_expectations(self):
        return self.environment.expectations.evaluate

    def config_dict_for_solid(self, name):
        check.str_param(name, 'name')
        if name not in self.environment.solids:
            return {}
        else:
            return self.environment.solids[name].config_dict


def execute_pipeline_iterator(pipeline, environment):
    check.inst_param(pipeline, 'pipeline', PipelineDefinition)
    check.inst_param(environment, 'enviroment', config.Environment)

    execution_graph = ExecutionGraph.from_pipeline(pipeline)
    env = DagsterEnv(execution_graph, environment)
    with env.yield_context() as context:
        return _execute_graph_iterator(context, execution_graph, env)


def _execute_graph_iterator(context, execution_graph, env):
    check.inst_param(context, 'context', ExecutionContext)
    check.inst_param(execution_graph, 'execution_graph', ExecutionGraph)
    check.inst_param(env, 'env', DagsterEnv)

    cn_graph = create_compute_node_graph_from_env(execution_graph, env)

    cn_nodes = list(cn_graph.topological_nodes())

    check.invariant(len(cn_nodes[0].node_inputs) == 0)

    solid = None
    solid_results = []
    for cn_result in execute_compute_nodes(context, cn_nodes):
        cn_node = cn_result.compute_node

        if solid and solid is not cn_node.solid:
            yield SolidExecutionResult.from_results(context, solid_results)
            solid_results = []

        if not cn_result.success:
            solid_results.append(cn_result)
            yield SolidExecutionResult.from_results(context, solid_results)
            solid_results = []
            return

        solid = cn_node.solid
        solid_results.append(cn_result)

    if solid and solid_results:
        yield SolidExecutionResult.from_results(context, solid_results)


def execute_pipeline(
    pipeline,
    environment,
    *,
    throw_on_error=True,
):
    '''
    "Synchronous" version of execute_pipeline_iteator.

    throw_on_error makes the function throw when an error is encoutered rather than returning
    the LegacySolidExecutionResult in an error-state.

    Note: throw_on_error is very useful in testing contexts when not testing for error conditions
    '''

    check.inst_param(pipeline, 'pipeline', PipelineDefinition)
    check.inst_param(environment, 'environment', config.Environment)
    execution_graph = ExecutionGraph.from_pipeline(pipeline)
    env = DagsterEnv(execution_graph, environment)
    return _execute_graph(execution_graph, env, throw_on_error)


def _execute_graph(
    execution_graph,
    env,
    throw_on_error=True,
):
    check.inst_param(execution_graph, 'execution_graph', ExecutionGraph)
    check.inst_param(env, 'env', DagsterEnv)
    check.bool_param(throw_on_error, 'throw_on_error')

    results = []
    with env.yield_context() as context:
        with context.value('pipeline', execution_graph.pipeline.name or '<<unnamed>>'):
            for result in _execute_graph_iterator(context, execution_graph, env):
                if throw_on_error:
                    if not result.success:
                        _do_throw_on_error(result)

                results.append(result)
            return PipelineExecutionResult(context, results)
