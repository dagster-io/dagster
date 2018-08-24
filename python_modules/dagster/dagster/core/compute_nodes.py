from collections import (namedtuple, defaultdict)
from contextlib import contextmanager
from enum import Enum
import uuid
import sys

import toposort

from dagster import check

from dagster.utils.indenting_printer import IndentingPrinter
from dagster.utils.logging import (get_formatted_stack_trace, define_logger)
from dagster.utils.timing import time_execution_scope

from .argument_handling import validate_args

from .definitions import (
    DependencyStructure,
    ExpectationDefinition,
    InputDefinition,
    OutputDefinition,
    Result,
    SolidDefinition,
    SolidOutputHandle,
)

from .execution_context import ExecutionContext

from .errors import (
    DagsterExpectationFailedError,
    DagsterInvariantViolationError,
    DagsterUserCodeExecutionError,
)

from .graph import ExecutionGraph

from .types import DagsterType

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


EXPECTATION_VALUE_OUTPUT = 'expectation_value'
JOIN_OUTPUT = 'join_output'
EXPECTATION_INPUT = 'expectation_input'


def _execute_core_transform(context, solid_name, solid_transform_fn, values_dict, config_dict):
    '''
    Execute the user-specified transform for the solid. Wrap in an error boundary and do
    all relevant logging and metrics tracking
    '''
    check.inst_param(context, 'context', ExecutionContext)
    check.str_param(solid_name, 'solid_name')
    check.callable_param(solid_transform_fn, 'solid_transform_fn')
    check.dict_param(values_dict, 'values_dict', key_type=str)
    check.dict_param(config_dict, 'config_dict', key_type=str)

    error_str = 'Error occured during core transform'
    with _user_code_error_boundary(context, error_str):
        with time_execution_scope() as timer_result:
            with context.value('solid', solid_name):
                gen = solid_transform_fn(context, values_dict, config_dict)
                if gen is not None:
                    for result in gen:
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
        self._node_input_dict = node_input_dict
        self.node_outputs = check.list_param(
            node_outputs, 'node_outputs', of_type=ComputeNodeOutput
        )

        node_output_dict = {}
        for node_output in node_outputs:
            node_output_dict[node_output.name] = node_output

        self._node_output_dict = node_output_dict
        self.arg_dict = check.dict_param(arg_dict, 'arg_dict', key_type=str)
        self.compute_fn = check.callable_param(compute_fn, 'compute_fn')
        self.tag = check.inst_param(tag, 'tag', ComputeNodeTag)
        self.solid = check.inst_param(solid, 'solid', SolidDefinition)

    def has_node(self, name):
        check.str_param(name, 'name')
        return name in self._node_output_dict

    def node_named(self, name):
        check.str_param(name, 'name')
        return self._node_output_dict[name]

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
            compute_node_input = self._node_input_dict[input_name]
            if not compute_node_input.dagster_type.is_python_valid_value(input_value):
                raise DagsterInvariantViolationError(
                    f'''Solid {self.solid.name} input {input_name}
                   received value {input_value} which does not match the type for Dagster type
                   {compute_node_input.dagster_type.name}. Compute node {self.friendly_name}'''
                )

        error_str = 'TODO error string'

        seen_outputs = set()

        try:

            with _user_code_error_boundary(context, error_str):
                gen = self.compute_fn(context, inputs)

            if gen is None:
                check.invariant(not self.node_outputs)
                return

            results = list(gen)

            for result in results:
                if not self.has_node(result.output_name):
                    raise DagsterInvariantViolationError(
                        f'''Core transform for {self.solid.name} returned an output
                        {result.output_name} that does not exist. The available
                        outputs are {list([output_def.name for output_def in self.solid.output_defs])}'''
                    )

                if result.output_name in seen_outputs:
                    raise DagsterInvariantViolationError(
                        f'''Core transform for {self.solid.name} returned an output
                        {result.output_name} multiple times'''
                    )

                seen_outputs.add(result.output_name)

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

                target_cn = prev_output_handle.compute_node

                check.failed(
                    f'Could not find handle {prev_output_handle} in results. ' + \
                    f'current node: {compute_node.friendly_name}\n' + \
                    f'target node: {target_cn.friendly_name}'
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


def create_expectation_cn(
    solid,
    expectation_def,
    friendly_name,
    tag,
    prev_node_output_handle,
    inout_def,
):

    check.inst_param(solid, 'solid', SolidDefinition)
    check.inst_param(expectation_def, 'input_expct_def', ExpectationDefinition)
    check.inst_param(prev_node_output_handle, 'prev_node_output_handle', ComputeNodeOutputHandle)
    check.inst_param(inout_def, 'inout_def', (InputDefinition, OutputDefinition))

    value_type = inout_def.dagster_type

    return SingleSyncOutputComputeNode(
        friendly_name=friendly_name,
        node_inputs=[
            ComputeNodeInput(
                name=EXPECTATION_INPUT,
                dagster_type=value_type,
                prev_output_handle=prev_node_output_handle,
            )
        ],
        node_outputs=[
            ComputeNodeOutput(name=EXPECTATION_VALUE_OUTPUT, dagster_type=value_type),
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
            inout_def=inout_def,
        )
        input_expect_nodes.append(expect_compute_node)
        compute_nodes.append(expect_compute_node)

    join_cn = _create_join_node(solid, input_expect_nodes, EXPECTATION_VALUE_OUTPUT)

    output_name = join_cn.node_outputs[0].name
    return ExpectationsComputeNodeGraph(
        compute_nodes + [join_cn],
        create_cn_output_handle(join_cn, output_name),
    )


def _prev_node_handle(dep_structure, solid, input_def, compute_node_output_map):
    check.inst_param(dep_structure, 'dep_structure', DependencyStructure)
    check.inst_param(solid, 'solid', SolidDefinition)
    check.inst_param(input_def, 'input_def', InputDefinition)
    check.inst_param(compute_node_output_map, 'compute_node_output_map', ComputeNodeOutputMap)

    input_handle = solid.input_handle(input_def.name)

    check.invariant(
        dep_structure.has_dep(input_handle),
        f'{input_handle} not found in dependency structure',
    )

    solid_output_handle = dep_structure.get_dep(input_handle)
    return compute_node_output_map[solid_output_handle]


def create_cn_output_handle(compute_node, cn_output_name):
    check.inst_param(compute_node, 'compute_node', ComputeNode)
    check.str_param(cn_output_name, 'cn_output_name')
    return ComputeNodeOutputHandle(compute_node, cn_output_name)


class ComputeNodeOutputMap(dict):
    def __getitem__(self, key):
        check.inst_param(key, 'key', SolidOutputHandle)
        return dict.__getitem__(self, key)

    def __setitem__(self, key, val):
        check.inst_param(key, 'key', SolidOutputHandle)
        check.inst_param(val, 'val', ComputeNodeOutputHandle)
        return dict.__setitem__(self, key, val)


def create_compute_node_graph_from_env(execution_graph, env):
    import dagster.core.execution
    check.inst_param(execution_graph, 'execution_graph', ExecutionGraph)
    check.inst_param(env, 'env', dagster.core.execution.DagsterEnv)

    dependency_structure = execution_graph.dependency_structure

    compute_nodes = []

    cn_output_node_map = ComputeNodeOutputMap()

    for topo_solid in execution_graph.topological_solids:
        cn_inputs = []

        for input_def in topo_solid.input_defs:
            prev_cn_output_handle = _prev_node_handle(
                dependency_structure,
                topo_solid,
                input_def,
                cn_output_node_map,
            )

            check.inst(prev_cn_output_handle, ComputeNodeOutputHandle)

            # jam in input expectations here

            if env.evaluate_expectations and input_def.expectations:
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

        validated_config_args = validate_args(
            topo_solid.config_def.argument_def_dict,
            env.config_dict_for_solid(topo_solid.name),
            'config for solid {solid_name}'.format(solid_name=topo_solid.name),
        )

        solid_transform_cn = create_compute_node_from_solid_transform(
            topo_solid,
            cn_inputs,
            validated_config_args,
        )

        for output_def in topo_solid.output_defs:
            output_handle = topo_solid.output_handle(output_def.name)
            if env.evaluate_expectations and output_def.expectations:
                expectations_graph = create_expectations_cn_graph(
                    topo_solid,
                    output_def,
                    create_cn_output_handle(solid_transform_cn, output_def.name),
                    tag=ComputeNodeTag.OUTPUT_EXPECTATION
                )
                compute_nodes = compute_nodes + expectations_graph.nodes
                cn_output_node_map[output_handle] = expectations_graph.terminal_cn_output_handle
            else:
                cn_output_node_map[output_handle] = create_cn_output_handle(
                    solid_transform_cn,
                    output_def.name,
                )

        compute_nodes.append(solid_transform_cn)

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


def create_compute_node_from_solid_transform(solid, node_inputs, config_args):
    check.inst_param(solid, 'solid', SolidDefinition)
    check.list_param(node_inputs, 'node_inputs', of_type=ComputeNodeInput)
    check.dict_param(config_args, 'config_args', key_type=str)

    return ComputeNode(
        friendly_name=f'{solid.name}.transform',
        node_inputs=node_inputs,
        node_outputs=[
            ComputeNodeOutput(name=output_def.name, dagster_type=output_def.dagster_type)
            for output_def in solid.output_defs
        ],
        arg_dict={},
        compute_fn=lambda context, inputs: _execute_core_transform(
            context,
            solid.name,
            solid.transform_fn,
            inputs,
            config_args,
        ),
        tag=ComputeNodeTag.TRANSFORM,
        solid=solid,
    )
