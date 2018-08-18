from collections import (namedtuple, defaultdict)
from contextlib import contextmanager
from enum import Enum
import uuid
import sys

import toposort

from dagster import (check, config)

from dagster.utils.indenting_printer import IndentingPrinter
from dagster.utils.logging import (get_formatted_stack_trace, define_logger)
from dagster.utils.timing import time_execution_scope

from .argument_handling import validate_args

from .definitions import (
    DependencyStructure,
    ExpectationDefinition,
    InputDefinition,
    MaterializationDefinition,
    OutputDefinition,
    PipelineDefinition,
    Result,
    SolidDefinition,
    SolidInputHandle,
    SolidOutputHandle,
)

from .execution_context import ExecutionContext

from .errors import (
    DagsterExpectationFailedError,
    DagsterInvariantViolationError,
    DagsterUserCodeExecutionError,
)

from .graph import create_subgraph

from .types import (
    Any,
    DagsterType,
)


def get_single_solid_output(solid):
    check.inst_param(solid, 'solid', SolidDefinition)
    check.invariant(len(solid.outputs) == 1)
    return solid.outputs[0]


class ComputeNodeOutputHandle(namedtuple('_ComputeNodeOutputHandle', 'compute_node output_name')):
    def __new__(cls, compute_node, output_name):
        return super(ComputeNodeOutputHandle, cls).__new__(
            cls,
            compute_node=check.inst_param(compute_node, 'compute_node', ComputeNode),
            output_name=check.str_param(output_name, 'output_name'),
        )

    # Make this hashable so it be a key in a dictionary

    def __str__(self):
        return f'ComputeNodeOutputHandle(guid="{self.compute_node.guid}", output_name="{self.output_name}")'

    def __hash__(self):
        return hash(self.compute_node.guid + self.output_name)

    def __eq__(self, other):
        return (
            self.compute_node.guid == other.compute_node.guid
            and self.output_name == other.output_name
        )


class ComputeNodeSuccessData(namedtuple('_ComputeNodeSuccessData', 'output_name value')):
    def __new__(cls, output_name, value):
        return super(ComputeNodeSuccessData, cls).__new__(
            cls,
            output_name=check.str_param(output_name, 'output_name'),
            value=value,
        )


class ComputeNodeFailureData(namedtuple('_ComputeNodeFailureData', 'dagster_user_exception')):
    def __new__(cls, dagster_user_exception):
        return super(ComputeNodeFailureData, cls).__new__(
            cls,
            dagster_user_exception=check.inst_param(
                dagster_user_exception,
                'dagster_user_exception',
                DagsterUserCodeExecutionError,
            ),
        )


class ComputeNodeResult(
    namedtuple(
        '_ComputeNodeResult',
        'success compute_node tag success_data failure_data ',
    )
):
    @staticmethod
    def success_result(compute_node, tag, success_data):
        return ComputeNodeResult(
            success=True,
            compute_node=check.inst_param(compute_node, 'compute_node', ComputeNode),
            tag=check.inst_param(tag, 'tag', ComputeNodeTag),
            success_data=check.inst_param(success_data, 'success_data', ComputeNodeSuccessData),
            failure_data=None,
        )

    @staticmethod
    def failure_result(compute_node, tag, failure_data):
        return ComputeNodeResult(
            success=False,
            compute_node=check.inst_param(compute_node, 'compute_node', ComputeNode),
            tag=check.inst_param(tag, 'tag', ComputeNodeTag),
            success_data=None,
            failure_data=check.inst_param(failure_data, 'failure_data', ComputeNodeFailureData),
        )


LOG_LEVEL = 'ERROR'
logger = define_logger('dagster-compute-nodes', LOG_LEVEL)


@contextmanager
def _user_code_error_boundary(context, msg, **kwargs):
    '''
    Wraps the execution of user-space code in an error boundary. This places a uniform
    policy around an user code invoked by the framework. This ensures that all user
    errors are wrapped in the SolidUserCodeExecutionError, and that the original stack
    trace of the user error is preserved, so that it can be reported without confusing
    framework code in the stack trace, if a tool author wishes to do so. This has
    been especially help in a notebooking context.
    '''
    check.inst_param(context, 'context', ExecutionContext)
    check.str_param(msg, 'msg')

    try:
        yield
    except Exception as e:
        stack_trace = get_formatted_stack_trace(e)
        context.error(str(e), stack_trace=stack_trace)
        raise DagsterUserCodeExecutionError(
            msg.format(**kwargs), e, user_exception=e, original_exc_info=sys.exc_info()
        )


class ComputeNodeTag(Enum):
    TRANSFORM = 'TRANSFORM'
    INPUT_EXPECTATION = 'INPUT_EXPECTATION'
    OUTPUT_EXPECTATION = 'OUTPUT_EXPECTATION'
    JOIN = 'JOIN'
    SOURCE = 'SOURCE'
    MATERIALIZATION = 'MATERIALIZATION'
    INPUTSTUB = 'INPUTSTUB'


EXPECTATION_VALUE_OUTPUT = 'expectation_value'
JOIN_OUTPUT = 'join_output'
MATERIALIZATION_INPUT = 'mat_input'
EXPECTATION_INPUT = 'expectation_input'


def _execute_core_transform(context, solid_transform_fn, values_dict):
    '''
    Execute the user-specified transform for the solid. Wrap in an error boundary and do
    all relevant logging and metrics tracking
    '''
    check.inst_param(context, 'context', ExecutionContext)
    check.callable_param(solid_transform_fn, 'solid_transform_fn')
    check.dict_param(values_dict, 'values_dict', key_type=str)

    error_str = 'Error occured during core transform'
    with _user_code_error_boundary(context, error_str):
        with time_execution_scope() as timer_result:
            for result in solid_transform_fn(context, values_dict):
                yield result

        context.metric('core_transform_time_ms', timer_result.millis)


class ComputeNodeInput:
    def __init__(self, name, dagster_type, prev_output_handle):
        self.name = check.str_param(name, 'name')
        self.dagster_type = check.inst_param(dagster_type, 'dagster_type', DagsterType)
        self.prev_output_handle = check.inst_param(
            prev_output_handle,
            'prev_output_handle',
            ComputeNodeOutputHandle,
        )


class ComputeNodeOutput:
    def __init__(self, name, dagster_type):
        self.name = check.str_param(name, 'name')
        self.dagster_type = check.inst_param(dagster_type, 'dagster_type', DagsterType)


class ComputeNode:
    def __init__(self, friendly_name, node_inputs, node_outputs, arg_dict, compute_fn, tag, solid):
        self.guid = str(uuid.uuid4())
        self.friendly_name = check.str_param(friendly_name, 'friendly_name')
        self.node_inputs = check.list_param(node_inputs, 'node_inputs', of_type=ComputeNodeInput)

        node_input_dict = {}
        for node_input in node_inputs:
            node_input_dict[node_input.name] = node_input
        self.node_input_dict = node_input_dict

        self.node_outputs = check.list_param(
            node_outputs, 'node_outputs', of_type=ComputeNodeOutput
        )

        self.arg_dict = check.dict_param(arg_dict, 'arg_dict', key_type=str)
        self.compute_fn = check.callable_param(compute_fn, 'compute_fn')
        self.tag = check.inst_param(tag, 'tag', ComputeNodeTag)
        self.solid = check.inst_param(solid, 'solid', SolidDefinition)

    def node_named(self, name):
        check.str_param(name, 'name')
        for node_output in self.node_outputs:
            if node_output.name == name:
                return node_output

        check.failed('not found')

    def _create_compute_node_result(self, result):
        check.inst_param(result, 'result', Result)

        node_output = self.node_named(result.output_name)

        if not node_output.dagster_type.is_python_valid_value(result.value):
            raise DagsterInvariantViolationError(
                f'''Solid {self.solid.name} output {result.value}
                which does not match the type for Dagster Type
                {node_output.dagster_type.name}'''
            )

        return ComputeNodeResult.success_result(
            compute_node=self,
            tag=self.tag,
            success_data=ComputeNodeSuccessData(
                output_name=result.output_name,
                value=result.value,
            ),
        )

    def execute(self, context, inputs):
        check.inst_param(context, 'context', ExecutionContext)
        check.dict_param(inputs, 'inputs', key_type=str)

        logger.debug(f'Entering execution for {self.friendly_name}')

        # do runtime type checks of inputs versus node inputs
        for input_name, input_value in inputs.items():
            compute_node_input = self.node_input_dict[input_name]
            if not compute_node_input.dagster_type.is_python_valid_value(input_value):
                raise DagsterInvariantViolationError(
                    f'''Solid {self.solid.name} input {input_name}
                   received value {input_value} which does not match the type for Dagster type
                   {compute_node_input.dagster_type.name}. Compute node {self.friendly_name}'''
                )

        error_str = 'TODO error string'

        try:
            with _user_code_error_boundary(context, error_str):
                results = list(self.compute_fn(context, inputs))

                if not self.node_outputs:
                    return

                for result in results:
                    yield self._create_compute_node_result(result)

        except DagsterUserCodeExecutionError as dagster_user_exception:
            yield ComputeNodeResult.failure_result(
                compute_node=self,
                tag=self.tag,
                failure_data=ComputeNodeFailureData(
                    dagster_user_exception=dagster_user_exception,
                ),
            )
            return

    def output_named(self, name):
        check.str_param(name, 'name')

        for node_output in self.node_outputs:
            if node_output.name == name:
                return node_output

        check.failed(f'output {name} not found')


def execute_compute_nodes(context, compute_nodes):
    check.inst_param(context, 'context', ExecutionContext)
    check.list_param(compute_nodes, 'compute_nodes', of_type=ComputeNode)

    intermediate_results = {}
    for compute_node in compute_nodes:
        input_values = {}
        for node_input in compute_node.node_inputs:
            prev_output_handle = node_input.prev_output_handle
            if prev_output_handle not in intermediate_results:
                check.failed(
                    f'Could not find handle {prev_output_handle} in results. ' + \
                    f'current node: {compute_node.friendly_name}'
                )
            input_value = intermediate_results[prev_output_handle].success_data.value
            input_values[node_input.name] = input_value

        for result in compute_node.execute(context, input_values):
            check.invariant(isinstance(result, ComputeNodeResult))
            yield result
            output_handle = create_cn_output_handle(compute_node, result.success_data.output_name)
            intermediate_results[output_handle] = result


def _yieldify(sync_compute_fn):
    def _wrap(context, inputs):
        yield sync_compute_fn(context, inputs)

    return _wrap


class SingleSyncOutputComputeNode(ComputeNode):
    def __init__(self, *, sync_compute_fn, **kwargs):
        super().__init__(compute_fn=_yieldify(sync_compute_fn), **kwargs)


def create_compute_node_from_source_config(solid, input_name, source_config):
    check.inst_param(solid, 'solid', SolidDefinition)
    check.str_param(input_name, 'input_name')
    check.inst_param(source_config, 'source_config', config.Source)

    input_def = solid.input_def_named(input_name)
    source_def = input_def.source_of_type(source_config.name)

    error_context_str = 'source type {source}'.format(source=source_def.source_type)

    arg_dict = validate_args(
        source_def.argument_def_dict,
        source_config.args,
        error_context_str,
    )

    return SingleSyncOutputComputeNode(
        friendly_name=f'{solid.name}.{input_name}.source.{source_config.name}',
        node_inputs=[],
        node_outputs=[
            ComputeNodeOutput(
                name=SOURCE_OUTPUT,
                dagster_type=input_def.dagster_type,
            ),
        ],
        arg_dict=arg_dict,
        sync_compute_fn=lambda context, _inputs: Result(
            output_name=SOURCE_OUTPUT,
            value=source_def.source_fn(context, arg_dict)
        ),
        tag=ComputeNodeTag.SOURCE,
        solid=solid,
    )


def create_source_compute_node_dict_from_environment(pipeline, environment):
    check.inst_param(pipeline, 'pipeline', PipelineDefinition)
    check.inst_param(environment, 'environment', config.Environment)

    source_cn_dict = {}
    for solid_name, sources_by_input in environment.sources.items():
        solid = pipeline.solid_named(solid_name)
        for input_name, source_config in sources_by_input.items():
            compute_node = create_compute_node_from_source_config(solid, input_name, source_config)
            source_cn_dict[solid.input_handle(input_name)] = compute_node
    return source_cn_dict


def get_lambda(output_name, value):
    return lambda _context, _args: Result(output_name, value)


SOURCE_OUTPUT = 'source_output'


def create_source_compute_node_dict_from_input_values(pipeline, input_values):
    check.inst_param(pipeline, 'pipeline', PipelineDefinition)
    check.dict_param(input_values, 'input_values', key_type=str)

    source_cn_dict = {}
    for solid_name, sources_by_input in input_values.items():
        solid = pipeline.solid_named(solid_name)
        for input_name, input_value in sources_by_input.items():
            input_handle = solid.input_handle(input_name)
            source_cn_dict[input_handle] = SingleSyncOutputComputeNode(
                friendly_name=f'{solid_name}.{input_name}.stub',
                node_inputs=[],
                # This is just a stub of a pre-existing value, so we are not
                # going to make any type guarantees
                node_outputs=[ComputeNodeOutput(SOURCE_OUTPUT, Any)],
                arg_dict={},
                sync_compute_fn=get_lambda(SOURCE_OUTPUT, input_value),
                tag=ComputeNodeTag.INPUTSTUB,
                solid=pipeline.solid_named(solid_name),
            )

    return source_cn_dict


def print_graph(graph, printer=print):
    check.inst_param(graph, 'graph', ComputeNodeGraph)
    printer = IndentingPrinter(printer=printer)

    for node in graph.topological_nodes():
        with printer.with_indent(f'Node {node.friendly_name} Id: {node.guid}'):
            for node_input in node.node_inputs:
                with printer.with_indent(f'Input: {node_input.name}'):
                    printer.line(f'Type: {node_input.dagster_type.name}')
                    printer.line(f'From: {node_input.prev_output_handle}')
            for node_output in node.node_outputs:
                with printer.with_indent(f'Output: {node_output.name}'):
                    printer.line(f'Type: {node_output.dagster_type.name}')


class ComputeNodeGraph:
    def __init__(self, cn_dict, deps):
        self.cn_dict = cn_dict
        self.deps = deps
        self.nodes = list(cn_dict.values())

    def topological_nodes(self):
        cn_guids_sorted = toposort.toposort_flatten(self.deps)
        for cn_guid in cn_guids_sorted:
            yield self.cn_dict[cn_guid]


def create_compute_node_graph_from_env(pipeline, env):
    import dagster.core.execution
    if isinstance(env, dagster.core.execution.ConfigEnv):
        return create_compute_node_graph_from_environment(
            pipeline,
            env.environment,
        )
    elif isinstance(env, dagster.core.execution.InMemoryEnv):
        return create_compute_node_graph_from_input_values(
            pipeline,
            env.input_values,
            from_solids=env.from_solids,
            through_solids=env.through_solids,
            evaluate_expectations=env.evaluate_expectations,
        )
    else:
        check.not_implemented('unsupported')


def create_compute_node_graph_from_input_values(
    pipeline,
    input_values,
    from_solids=None,
    through_solids=None,
    evaluate_expectations=True,
):
    source_cn_dict = create_source_compute_node_dict_from_input_values(pipeline, input_values)
    return create_compute_node_graph_from_source_dict(
        pipeline,
        source_cn_dict,
        from_solids=from_solids,
        through_solids=through_solids,
        evaluate_expectations=evaluate_expectations,
    )


def create_compute_node_graph_from_environment(pipeline, environment):
    source_cn_dict = create_source_compute_node_dict_from_environment(pipeline, environment)

    return create_compute_node_graph_from_source_dict(
        pipeline,
        source_cn_dict,
        materializations=environment.materializations,
        from_solids=environment.execution.from_solids,
        through_solids=environment.execution.through_solids,
        evaluate_expectations=environment.expectations.evaluate,
    )


def create_expectation_cn(solid, expectation_def, friendly_name, tag, prev_node_output_handle):
    check.inst_param(solid, 'solid', SolidDefinition)
    check.inst_param(expectation_def, 'input_expct_def', ExpectationDefinition)
    check.inst_param(prev_node_output_handle, 'prev_node_output_handle', ComputeNodeOutputHandle)

    output = get_single_solid_output(solid)

    return SingleSyncOutputComputeNode(
        friendly_name=friendly_name,
        node_inputs=[
            ComputeNodeInput(
                name=EXPECTATION_INPUT,
                dagster_type=output.dagster_type,
                prev_output_handle=prev_node_output_handle,
            )
        ],
        node_outputs=[
            ComputeNodeOutput(name=EXPECTATION_VALUE_OUTPUT, dagster_type=output.dagster_type),
        ],
        arg_dict={},
        sync_compute_fn=_create_expectation_lambda(
            solid,
            expectation_def,
            EXPECTATION_VALUE_OUTPUT,
        ),
        tag=tag,
        solid=solid
    )


ExpectationsComputeNodeGraph = namedtuple(
    'ExpectationsComputeNodeGraph',
    'nodes terminal_cn_output_handle',
)


def create_expectations_cn_graph(solid, inout_def, prev_node_output_handle, tag):
    check.inst_param(solid, 'solid', SolidDefinition)
    check.inst_param(inout_def, 'inout_def', (InputDefinition, OutputDefinition))
    check.inst_param(prev_node_output_handle, 'prev_node_output_handle', ComputeNodeOutputHandle)
    check.inst_param(tag, 'tag', ComputeNodeTag)

    compute_nodes = []
    input_expect_nodes = []
    for expectation_def in inout_def.expectations:
        expect_compute_node = create_expectation_cn(
            solid=solid,
            expectation_def=expectation_def,
            friendly_name=f'{solid.name}.{inout_def.name}.expectation.{expectation_def.name}',
            tag=tag,
            prev_node_output_handle=prev_node_output_handle,
        )
        input_expect_nodes.append(expect_compute_node)
        compute_nodes.append(expect_compute_node)

    join_cn = _create_join_node(solid, input_expect_nodes, EXPECTATION_VALUE_OUTPUT)

    output_name = join_cn.node_outputs[0].name
    return ExpectationsComputeNodeGraph(
        compute_nodes + [join_cn],
        create_cn_output_handle(join_cn, output_name),
    )


def _prev_node_handle(dep_structure, solid, input_def, source_cn_dict, logical_output_mapper):
    check.inst_param(dep_structure, 'dep_structure', DependencyStructure)
    check.inst_param(solid, 'solid', SolidDefinition)
    check.inst_param(input_def, 'input_def', InputDefinition)
    check.dict_param(
        source_cn_dict,
        'source_cn_dict',
        key_type=SolidInputHandle,
        value_type=ComputeNode,
    )

    check.inst_param(logical_output_mapper, 'mapper', LogicalSolidOutputMapper)

    input_handle = solid.input_handle(input_def.name)

    if input_handle in source_cn_dict:
        return create_cn_output_handle(source_cn_dict[input_handle], SOURCE_OUTPUT)
    else:
        check.invariant(
            dep_structure.has_dep(input_handle),
            f'{input_handle} not found in dependency structure',
        )

        solid_output_handle = dep_structure.get_dep(input_handle)
        return logical_output_mapper.get_cn_output_handle(solid_output_handle)


def create_cn_output_handle(compute_node, cn_output_name):
    check.inst_param(compute_node, 'compute_node', ComputeNode)
    check.str_param(cn_output_name, 'cn_output_name')
    return ComputeNodeOutputHandle(compute_node, cn_output_name)


class LogicalSolidOutputMapper:
    def __init__(self):
        self._output_handles = {}

    def set_mapping(self, solid_output_handle, cn_output_handle):
        check.inst_param(solid_output_handle, 'solid_output_handle', SolidOutputHandle)
        check.inst_param(cn_output_handle, 'cn_output_handle', ComputeNodeOutputHandle)
        self._output_handles[solid_output_handle] = cn_output_handle

    def get_cn_output_handle(self, solid_output_handle):
        check.inst_param(solid_output_handle, 'solid_output_handle', SolidOutputHandle)
        return self._output_handles[solid_output_handle]


def create_compute_node_graph_from_source_dict(
    pipeline,
    source_cn_dict,
    materializations=None,
    from_solids=None,
    through_solids=None,
    evaluate_expectations=True,
):

    check.inst_param(pipeline, 'pipeline', PipelineDefinition)

    check.dict_param(
        source_cn_dict,
        'source_cn_dict',
        key_type=SolidInputHandle,
        value_type=ComputeNode,
    )

    materializations = check.opt_list_param(
        materializations,
        'materializations',
        of_type=config.Materialization,
    )

    dep_structure = pipeline.dependency_structure

    check.bool_param(evaluate_expectations, 'evaluate_expectations')

    compute_nodes = list(source_cn_dict.values())

    logical_output_mapper = LogicalSolidOutputMapper()

    subgraph = create_subgraph(
        pipeline,
        check.opt_list_param(from_solids, 'from_solid', of_type=str),
        check.opt_list_param(through_solids, 'through_solid', of_type=str),
    )

    for topo_solid in subgraph.topological_solids:
        cn_inputs = []

        for input_def in topo_solid.inputs:
            prev_cn_output_handle = _prev_node_handle(
                dep_structure,
                topo_solid,
                input_def,
                source_cn_dict,
                logical_output_mapper,
            )

            check.inst(prev_cn_output_handle, ComputeNodeOutputHandle)

            # jam in input expectations here

            if evaluate_expectations and input_def.expectations:
                expectations_graph = create_expectations_cn_graph(
                    topo_solid,
                    input_def,
                    prev_cn_output_handle,
                    tag=ComputeNodeTag.INPUT_EXPECTATION,
                )
                compute_nodes = compute_nodes + expectations_graph.nodes

                check.inst(expectations_graph.terminal_cn_output_handle, ComputeNodeOutputHandle)

                cn_output_handle = expectations_graph.terminal_cn_output_handle
            else:
                cn_output_handle = prev_cn_output_handle

            cn_inputs.append(
                ComputeNodeInput(input_def.name, input_def.dagster_type, cn_output_handle)
            )

        solid_transform_cn = create_compute_node_from_solid_transform(topo_solid, cn_inputs)

        for output_def in topo_solid.outputs:
            if evaluate_expectations and output_def.expectations:
                expectations_graph = create_expectations_cn_graph(
                    topo_solid,
                    output_def,
                    create_cn_output_handle(solid_transform_cn, output_def.name),
                    tag=ComputeNodeTag.OUTPUT_EXPECTATION
                )
                compute_nodes = compute_nodes + expectations_graph.nodes
                logical_output_mapper.set_mapping(
                    topo_solid.output_handle(output_def.name),
                    expectations_graph.terminal_cn_output_handle,
                )
            else:
                logical_output_mapper.set_mapping(
                    topo_solid.output_handle(output_def.name),
                    create_cn_output_handle(solid_transform_cn, output_def.name),
                )

        compute_nodes.append(solid_transform_cn)

    for materialization in materializations:
        mat_solid = pipeline.solid_named(materialization.solid)
        mat_cn = _construct_materialization_cn(
            pipeline,
            materialization,
            logical_output_mapper.get_cn_output_handle(
                mat_solid.output_handle(materialization.output_name)
            ),
        )
        compute_nodes.append(mat_cn)

    cn_dict = {}
    for cn in compute_nodes:
        cn_dict[cn.guid] = cn

    deps = defaultdict(set)

    for cn in compute_nodes:
        deps[cn.guid] = set()
        for cn_input in cn.node_inputs:
            deps[cn.guid].add(cn_input.prev_output_handle.compute_node.guid)

    return ComputeNodeGraph(cn_dict, deps)


def _create_join_node(solid, prev_nodes, prev_output_name):
    check.inst_param(solid, 'solid', SolidDefinition)
    check.list_param(prev_nodes, 'prev_nodes', of_type=ComputeNode)
    check.invariant(len(prev_nodes) > 0)
    check.str_param(prev_output_name, 'output_name')

    node_inputs = []
    seen_dagster_type = None
    for prev_node in prev_nodes:
        prev_node_output = prev_node.output_named(prev_output_name)

        if seen_dagster_type is None:
            seen_dagster_type = prev_node_output.dagster_type
        else:
            check.invariant(seen_dagster_type == prev_node_output.dagster_type)

        output_handle = create_cn_output_handle(prev_node, prev_output_name)

        node_inputs.append(
            ComputeNodeInput(prev_node.guid, prev_node_output.dagster_type, output_handle)
        )

    return SingleSyncOutputComputeNode(
        friendly_name='join',
        node_inputs=node_inputs,
        node_outputs=[ComputeNodeOutput(JOIN_OUTPUT, seen_dagster_type)],
        arg_dict={},
        sync_compute_fn=_create_join_lambda,
        tag=ComputeNodeTag.JOIN,
        solid=solid,
    )


ExpectationExecutionInfo = namedtuple('ExpectationExecutionInfo', 'solid expectation_def')


def _create_join_lambda(_context, inputs):
    return Result(output_name=JOIN_OUTPUT, value=list(inputs.values())[0])


def _create_expectation_lambda(solid, expectation_def, output_name):
    check.inst_param(solid, 'solid', SolidDefinition)
    check.inst_param(expectation_def, 'expectations_def', ExpectationDefinition)
    check.str_param(output_name, 'output_name')

    def _do_expectation(context, inputs):
        expt_result = expectation_def.expectation_fn(
            context,
            ExpectationExecutionInfo(solid, expectation_def),
            inputs[EXPECTATION_INPUT],
        )
        if expt_result.success:
            return Result(output_name=output_name, value=inputs[EXPECTATION_INPUT])

        raise DagsterExpectationFailedError(None)  # for now

    return _do_expectation


def _construct_materialization_cn(pipeline, materialization, prev_output_handle):
    check.inst_param(pipeline, 'pipeline', PipelineDefinition)
    check.inst_param(materialization, 'materialization', config.Materialization)
    check.inst_param(prev_output_handle, 'prev_output_handle', ComputeNodeOutputHandle)

    solid = pipeline.solid_named(materialization.solid)
    output = get_single_solid_output(solid)
    mat_def = output.materialization_of_type(materialization.name)

    error_context_str = 'source type {mat}'.format(mat=mat_def.name)

    arg_dict = validate_args(
        mat_def.argument_def_dict,
        materialization.args,
        error_context_str,
    )

    return SingleSyncOutputComputeNode(
        friendly_name=f'{solid.name}.materialization.{mat_def.name}',
        node_inputs=[
            ComputeNodeInput(
                name=MATERIALIZATION_INPUT,
                dagster_type=output.dagster_type,
                prev_output_handle=prev_output_handle,
            )
        ],
        node_outputs=[],
        arg_dict=arg_dict,
        sync_compute_fn=_create_materialization_lambda(mat_def, materialization, 'TODO_REMOVE'),
        tag=ComputeNodeTag.MATERIALIZATION,
        solid=solid,
    )


def _create_materialization_lambda(mat_def, materialization, output_name):
    check.inst_param(mat_def, 'mat_def', MaterializationDefinition)
    check.inst_param(materialization, 'materialization', config.Materialization)
    check.str_param(output_name, 'output_name')

    return lambda context, inputs: Result(
        output_name=output_name,
        value=mat_def.materialization_fn(
            context,
            materialization.args,
            inputs[MATERIALIZATION_INPUT],
        ),
    )


def create_compute_node_from_solid_transform(solid, node_inputs):
    check.inst_param(solid, 'solid', SolidDefinition)
    check.list_param(node_inputs, 'node_inputs', of_type=ComputeNodeInput)

    return ComputeNode(
        friendly_name=f'{solid.name}.transform',
        node_inputs=node_inputs,
        node_outputs=[
            ComputeNodeOutput(name=output.name, dagster_type=output.dagster_type)
            for output in solid.outputs
        ],
        arg_dict={},
        compute_fn=lambda context, inputs: _execute_core_transform(
            context,
            solid.transform_fn,
            inputs,
        ),
        tag=ComputeNodeTag.TRANSFORM,
        solid=solid,
    )
