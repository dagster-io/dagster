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
    SolidDefinition,
    Solid,
)

from .errors import (
    DagsterEvaluateValueError,
    DagsterInvariantViolationError,
    DagsterTypeError,
    DagsterUserCodeExecutionError,
)

from .compute_nodes import (
    ComputeNodeExecutionInfo,
    ComputeNodeResult,
    ComputeNodeTag,
    create_compute_node_graph,
    execute_compute_nodes,
)

from .execution_context import ExecutionContext


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
        self.context = check.inst_param(context, 'context', ExecutionContext)
        self.result_list = check.list_param(
            result_list, 'result_list', of_type=SolidExecutionResult
        )

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
        self.context = check.inst_param(context, 'context', ExecutionContext)
        self.solid = check.inst_param(solid, 'solid', Solid)
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


def _wrap_in_yield(context_or_generator):
    if isinstance(context_or_generator, ExecutionContext):

        def _wrap():
            yield context_or_generator

        return _wrap()

    return context_or_generator


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


def _create_config_value(config_type, config_input):
    try:
        return config_type.evaluate_value(config_input)
    except DagsterEvaluateValueError as e:
        raise DagsterTypeError(
            'Invalid config value: {error_msg}'.format(error_msg=','.join(e.args))
        )


@contextmanager
def yield_context(pipeline, environment):
    check.inst_param(pipeline, 'pipeline', PipelineDefinition)
    check.inst_param(environment, 'environment', config.Environment)

    _validate_environment(environment, pipeline)

    context_name = environment.context.name
    context_definition = pipeline.context_definitions[context_name]
    config_type = context_definition.config_def.config_type

    config_value = _create_config_value(config_type, environment.context.config)
    context_or_generator = context_definition.context_fn(
        ContextCreationExecutionInfo(
            config=config_value,
            pipeline_def=pipeline,
        )
    )
    return _wrap_in_yield(context_or_generator)


def execute_pipeline_iterator(pipeline, environment):
    '''Returns iterator that yields :py:class:`SolidExecutionResult` for each
    solid executed in the pipeline.

    Parameters:
      pipeline (PipelineDefinition): pipeline to run
      execution (ExecutionContext): execution context of the run
    '''
    check.inst_param(pipeline, 'pipeline', PipelineDefinition)
    check.inst_param(environment, 'enviroment', config.Environment)

    execution_graph = ExecutionGraph.from_pipeline(pipeline)
    with yield_context(pipeline, environment) as context:
        return _execute_graph_iterator(context, execution_graph, environment)


def _execute_graph_iterator(context, execution_graph, environment):
    check.inst_param(context, 'context', ExecutionContext)
    check.inst_param(execution_graph, 'execution_graph', ExecutionGraph)
    check.inst_param(environment, 'environent', config.Environment)

    cn_graph = create_compute_node_graph(
        ComputeNodeExecutionInfo(
            context,
            execution_graph,
            environment,
        ),
    )

    cn_nodes = list(cn_graph.topological_nodes())

    if not cn_nodes:
        context.debug(
            'Pipeline {pipeline} has no nodes and no execution will happen'.format(
                pipeline=execution_graph.pipeline.display_name
            )
        )
        return

    context.debug(
        'About to execute the compute node graph in the following order {order}'.format(
            order=[cn.friendly_name for cn in cn_nodes]
        )
    )

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
    environment=None,
    throw_on_error=True,
):
    '''
    "Synchronous" version of `execute_pipeline_iterator`.

    Note: throw_on_error is very useful in testing contexts when not testing for error conditions

    Parameters:
      pipeline (PipelineDefinition): pipeline to run
      execution (ExecutionContext): execution context of the run
      throw_on_error (bool):
        throw_on_error makes the function throw when an error is encoutered rather than returning
        the py:class:`SolidExecutionResult` in an error-state.


    Returns:
      PipelineExecutionResult
    '''

    check.inst_param(pipeline, 'pipeline', PipelineDefinition)
    environment = check.opt_inst_param(
        environment,
        'environment',
        config.Environment,
        config.Environment(),
    )
    execution_graph = ExecutionGraph.from_pipeline(pipeline)
    return _execute_graph(execution_graph, environment, throw_on_error)


def _execute_graph(
    execution_graph,
    environment,
    throw_on_error=True,
):
    check.inst_param(execution_graph, 'execution_graph', ExecutionGraph)
    check.inst_param(environment, 'environment', config.Environment)
    check.bool_param(throw_on_error, 'throw_on_error')

    display_name = execution_graph.pipeline.display_name
    results = []
    with yield_context(execution_graph.pipeline, environment) as context, \
         context.value('pipeline', execution_graph.pipeline.display_name):

        context.info('Beginning execution of pipeline {pipeline}'.format(pipeline=display_name))

        for result in _execute_graph_iterator(context, execution_graph, environment):
            if throw_on_error and not result.success:
                result.reraise_user_error()

            results.append(result)

        pipeline_result = PipelineExecutionResult(execution_graph.pipeline, context, results)
        if pipeline_result.success:
            context.info(
                'Completing successful execution of pipeline {pipeline}'.format(
                    pipeline=display_name
                )
            )
        else:
            context.info(
                'Completing failing execution of pipeline {pipeline}'.format(pipeline=display_name)
            )

        return pipeline_result
