'''
Naming conventions:

For public functions:

execute_*

These represent functions which do purely in-memory compute. They will evaluate expectations
the core transform, and exercise all logging and metrics tracking (outside of outputs), but they
will not invoke *any* outputs (and their APIs don't allow the user to).

materialize_*

Materializations functions do execution but also allow the user to specify materializations,
which create artifacts that are discoverable by external systems (e.g. files, database
tables, and so on).


'''

# too many lines
# pylint: disable=C0302

from contextlib import contextmanager
import copy

import six

from dagster import check, config

from .definitions import (
    SolidDefinition,
    PipelineDefinition,
    PipelineContextDefinition,
)

from .errors import (
    DagsterUserCodeExecutionError,
    DagsterExecutionFailureReason,
    DagsterExpectationFailedError,
    DagsterInvariantViolationError,
)

from .argument_handling import validate_args

from .compute_nodes import (
    ComputeNodeTag,
    create_compute_node_graph_from_env,
    execute_compute_nodes,
)

from .execution_context import ExecutionContext

class DagsterPipelineExecutionResult:
    def __init__(
        self,
        context,
        result_list,
    ):
        self.context = check.inst_param(context, 'context', ExecutionContext)
        self.result_list = check.list_param(
            result_list, 'result_list', of_type=ExecutionStepResult
        )

    @property
    def success(self):
        return all([result.success for result in self.result_list])

    def result_named(self, name):
        check.str_param(name, 'name')
        for result in self.result_list:
            if result.name == name:
                return result
        check.failed('Did not find result {name} in pipeline execution result'.format(name=name))


class ExecutionStepResult:
    def __init__(self, *, success, context, transformed_value, name, dagster_user_exception, solid, tag, output_name):
        self.success = check.bool_param(success, 'success')
        self.context = context
        self.transformed_value = transformed_value
        self.name = name
        self.dagster_user_exception = dagster_user_exception
        self.solid = solid
        self.tag = tag
        self.output_name = output_name

    def copy(self):
        ''' This must be used instead of copy.deepcopy() because exceptions cannot
        be deepcopied'''
        return ExecutionStepResult(
            name=self.name,
            solid=self.solid,
            success=self.success,
            transformed_value=copy.deepcopy(self.transformed_value),
            context=self.context,
            dagster_user_exception=self.dagster_user_exception,
            tag=self.tag,
            output_name=self.output_name
        )

    def reraise_user_error(self):
        check.inst(self.dagster_user_exception, DagsterUserCodeExecutionError)
        six.reraise(*self.dagster_user_exception.original_exc_info)


def copy_result_list(result_list):
    if result_list is None:
        return result_list

    return [result.copy() for result in result_list]


def copy_result_dict(result_dict):
    if result_dict is None:
        return None
    new_dict = {}
    for input_name, result in result_dict.items():
        new_dict[input_name] = result.copy()
    return new_dict


def _create_passthrough_context_definition(context):
    check.inst_param(context, 'context', ExecutionContext)
    context_definition = PipelineContextDefinition(
        argument_def_dict={},
        context_fn=lambda _pipeline, _args: context
    )
    return {'default': context_definition}


def execute_single_solid(context, solid, environment, throw_on_error=True):
    check.inst_param(context, 'context', ExecutionContext)
    check.inst_param(solid, 'solid', SolidDefinition)
    check.inst_param(environment, 'environment', config.Environment)
    check.bool_param(throw_on_error, 'throw_on_error')

    check.invariant(environment.execution.from_solids == [])
    check.invariant(environment.execution.through_solids == [])

    single_solid_environment = config.Environment(
        sources=environment.sources,
        materializations=environment.materializations,
        expectations=environment.expectations,
        context=environment.context,
        execution=config.Execution.single_solid(solid.name),
    )

    pipeline_result = execute_pipeline(
        PipelineDefinition(
            solids=[solid],
            context_definitions=_create_passthrough_context_definition(context),
        ),
        environment=single_solid_environment,
    )

    results = pipeline_result.result_list
    check.invariant(len(results) == 1, 'must be one result got ' + str(len(results)))
    return results[0]


def _do_throw_on_error(execution_result):
    check.inst_param(execution_result, 'execution_result', ExecutionStepResult)
    if execution_result.success:
        return

    if isinstance(execution_result.dagster_user_exception, DagsterUserCodeExecutionError):
        execution_result.reraise_user_error()

    raise execution_result.dagster_user_exception

def output_single_solid(
    context,
    solid,
    environment,
    name,
    arg_dict,
    throw_on_error=True,
):
    check.inst_param(context, 'context', ExecutionContext)
    check.inst_param(solid, 'solid', SolidDefinition)
    check.inst_param(environment, 'environment', config.Environment)
    check.str_param(name, 'name')
    check.dict_param(arg_dict, 'arg_dict', key_type=str)
    check.bool_param(throw_on_error, 'throw_on_error')


    results = list(
        execute_pipeline_iterator(
            PipelineDefinition(
                solids=[solid],
                context_definitions=_create_passthrough_context_definition(context),
            ),
            environment=config.Environment(
                context=environment.context,
                sources=environment.sources,
                materializations=[
                    config.Materialization(
                        solid=solid.name, name=name, args=arg_dict
                    )
                ],
            ),
        )
    )

    for result in results:
        if not result.success:
            if throw_on_error:
                _do_throw_on_error(result)
            else:
                return result

    for result in results:
        if result.name == solid.name and result.tag == ComputeNodeTag.TRANSFORM:
            return result

    check.invariant(len(results) == 1, 'must be one result got ' + str(len(results)))

    execution_result = results[0]

    check.invariant(execution_result.name == solid.name)

    if throw_on_error:
        _do_throw_on_error(execution_result)

    return execution_result

class DagsterEnv:
    @contextmanager
    def yield_context(self):
        check.not_implemented('must implement in subclass')

    @property
    def materializations(self):
        check.not_implemented('must implement in subclass')

    @property
    def evaluate_expectations(self):
        check.not_implemented('must implement in subclass')

    @property
    def from_solids(self):
        check.not_implemented('must implement in subclass')

    @property
    def through_solids(self):
        check.not_implemented('must implement in subclass')

def _wrap_in_yield(thing):
    if isinstance(thing, ExecutionContext):
        def _wrap():
            yield thing

        return _wrap()

    return thing


class InMemoryEnv(DagsterEnv):
    def __init__(self, context, pipeline, input_values, from_solids=None, through_solids=None):
        super().__init__()
        self.context = check.inst_param(context, 'context', ExecutionContext)
        self.pipeline = check.inst_param(pipeline, 'pipeline', PipelineDefinition)
        self.input_values = check.dict_param(input_values, 'input_values', key_type=str)
        self._from_solids = check.opt_list_param(from_solids, from_solids, of_type=str)
        self._through_solids = check.opt_list_param(through_solids, through_solids, of_type=str)

    @property
    def from_solids(self):
        return self._from_solids

    @property
    def through_solids(self):
        return self._through_solids

    @contextmanager
    def yield_context(self):
        return _wrap_in_yield(self.context)

    @property
    def materializations(self):
        return []

    @property
    def evaluate_expectations(self):
        return True


def _validate_environment(environment, pipeline):
    for solid_name, input_configs in environment.sources.items():
        if not pipeline.has_solid(solid_name):
            raise DagsterInvariantViolationError(
                f'Solid "{solid_name} not found'
            )

        solid_inst = pipeline.solid_named(solid_name)

        for input_name, _source_configs in input_configs.items():
            if not solid_inst.has_input(input_name):
                raise DagsterInvariantViolationError(
                    f'Input "{input_name}" not found in the pipeline on solid "{solid_name}".' + \
                    f'Input must be one of {repr([inp.name for inp in solid_inst.inputs])}'
                )

    context_name = environment.context.name

    if context_name not in pipeline.context_definitions:
        avaiable_context_keys = list(pipeline.context_definitions.keys())
        raise DagsterInvariantViolationError(f'Context {context_name} not found in ' + \
            f'pipeline definiton. Available contexts {repr(avaiable_context_keys)}'
        )


class ConfigEnv(DagsterEnv):
    def __init__(self, pipeline, environment):
        super().__init__()
        # This is not necessarily the best spot for these calls
        _validate_environment(environment, pipeline)
        self.pipeline = check.inst_param(pipeline, 'pipeline', PipelineDefinition)
        self.environment = check.inst_param(environment, 'environment', config.Environment)

    @property
    def from_solids(self):
        return self.environment.execution.from_solids

    @property
    def through_solids(self):
        return self.environment.execution.through_solids

    @contextmanager
    def yield_context(self):
        context_name = self.environment.context.name
        context_definition = self.pipeline.context_definitions[context_name]

        args_to_pass = validate_args(
            self.pipeline.context_definitions[context_name].argument_def_dict,
            self.environment.context.args,
            'pipeline {pipeline_name} context {context_name}'.format(
                pipeline_name=self.pipeline.name,
                context_name=context_name,
            )
        )

        thing = context_definition.context_fn(self.pipeline, args_to_pass)
        return _wrap_in_yield(thing)

    @property
    def materializations(self):
        return self.environment.materializations

    @property
    def evaluate_expectations(self):
        return self.environment.expectations.evaluate

def execute_pipeline_iterator(pipeline, environment):
    check.inst_param(pipeline, 'pipeline', PipelineDefinition)
    check.inst_param(environment, 'enviroment', config.Environment)

    env = ConfigEnv(pipeline, environment)
    with env.yield_context() as context:
        return _execute_pipeline_iterator(
            context,
            pipeline,
            ConfigEnv(pipeline, environment)
        )

def execute_pipeline_iterator_in_memory(
    context,
    pipeline,
    input_values,
    *,
    from_solids=None,
    through_solids=None,
):
    check.opt_list_param(from_solids, 'from_solids', of_type=str)
    check.opt_list_param(through_solids, 'through_solids', of_type=str)
    return _execute_pipeline_iterator(
        context,
        pipeline,
        InMemoryEnv(context, pipeline, input_values, from_solids, through_solids),
    )


def _execute_pipeline_iterator(context, pipeline, env):
    check.inst_param(context, 'context', ExecutionContext)
    check.inst_param(pipeline, 'pipeline', PipelineDefinition)
    check.inst_param(env, 'env', DagsterEnv)


    cn_graph = create_compute_node_graph_from_env(pipeline, env)

    cn_nodes = list(cn_graph.topological_nodes())

    check.invariant(len(cn_nodes[0].node_inputs) == 0)

    for cn_result in execute_compute_nodes(context, cn_nodes):
        cn_node = cn_result.compute_node
        if not cn_result.success:
            yield ExecutionStepResult(
                success=False,
                context=context,
                transformed_value=None,
                name=cn_node.solid.name,
                dagster_user_exception=cn_result.failure_data.dagster_user_exception,
                solid=cn_node.solid,
                tag=cn_result.tag,
                output_name=None
            )
            return

        if cn_node.tag == ComputeNodeTag.TRANSFORM:
            yield ExecutionStepResult(
                success=True,
                context=context,
                transformed_value=cn_result.success_data.value,
                name=cn_node.solid.name,
                dagster_user_exception=None,
                solid=cn_node.solid,
                tag=cn_node.tag,
                output_name=cn_result.success_data.output_name,
            )

def execute_pipeline(
    pipeline,
    environment,
    *,
    throw_on_error=True,
):
    check.inst_param(environment, 'environment', config.Environment)
    return _execute_pipeline(
        pipeline,
        ConfigEnv(pipeline, environment),
        throw_on_error,
    )

def execute_pipeline_in_memory(
    context,
    pipeline,
    *,
    input_values,
    from_solids=None,
    through_solids=None,
    throw_on_error=True,
):
    check.dict_param(input_values, 'input_values', key_type=str)
    return _execute_pipeline(
        pipeline,
        InMemoryEnv(context, pipeline, input_values, from_solids, through_solids),
        throw_on_error,
    )

def _execute_pipeline(
    pipeline,
    env,
    throw_on_error=True,
):
    '''
    "Synchronous" version of execute_pipeline_iteator.

    throw_on_error makes the function throw when an error is encoutered rather than returning
    the LegacySolidExecutionResult in an error-state.

    Note: throw_on_error is very useful in testing contexts when not testing for error conditions
    '''
    check.inst_param(pipeline, 'pipeline', PipelineDefinition)
    check.inst_param(env, 'env', DagsterEnv)
    check.bool_param(throw_on_error, 'throw_on_error')

    results = []
    with env.yield_context() as context:
        for result in _execute_pipeline_iterator(
            context,
            pipeline,
            env=env,
        ):
            if throw_on_error:
                if not result.success:
                    _do_throw_on_error(result)

            results.append(result.copy())
        return DagsterPipelineExecutionResult(context, results)
