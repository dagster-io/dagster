from __future__ import print_function
from collections import (namedtuple, defaultdict)
from contextlib import contextmanager
from enum import Enum
import uuid
import sys

from future.utils import raise_from

import toposort

from dagster import (
    check,
    config,
)

from dagster.utils.indenting_printer import IndentingPrinter
from dagster.utils.logging import (
    get_formatted_stack_trace,
    define_colored_console_logger,
    ERROR,
)

from dagster.utils.timing import time_execution_scope

from .definitions import (
    ExecutionGraph,
    ExpectationDefinition,
    ExpectationExecutionInfo,
    InputDefinition,
    OutputDefinition,
    Result,
    SolidDefinition,
    SolidOutputHandle,
    Solid,
    TransformExecutionInfo,
)

from .execution_context import (
    ExecutionContext,
)

from .errors import (
    DagsterError,
    DagsterExpectationFailedError,
    DagsterInvariantViolationError,
    DagsterTypeError,
    DagsterUserCodeExecutionError,
    DagsterEvaluateValueError,
)

from .types import DagsterType


class ComputeNodeExecutionInfo(
    namedtuple('_ComputeNodeExecutionInfo', 'context execution_graph environment')
):
    def __new__(cls, context, execution_graph, environment):
        return super(ComputeNodeExecutionInfo, cls).__new__(
            cls,
            check.inst_param(context, 'context', ExecutionContext),
            check.inst_param(execution_graph, 'execution_graph', ExecutionGraph),
            check.inst_param(environment, 'environment', config.Environment),
        )

    @property
    def pipeline(self):
        return self.execution_graph.pipeline


class ComputeNodeOutputHandle(namedtuple('_ComputeNodeOutputHandle', 'compute_node output_name')):
    def __new__(cls, compute_node, output_name):
        return super(ComputeNodeOutputHandle, cls).__new__(
            cls,
            compute_node=check.inst_param(compute_node, 'compute_node', ComputeNode),
            output_name=check.str_param(output_name, 'output_name'),
        )

    # Make this hashable so it be a key in a dictionary

    def __str__(self):
        return (
            'ComputeNodeOutputHandle'
            '(cn="{cn.compute_node.friendly_name}", output_name="{cn.output_name}")'.format(
                cn=self
            )
        )

    def __repr__(self):
        return (
            'ComputeNodeOutputHandle'
            '(cn="{cn.compute_node.friendly_name}", output_name="{cn.output_name}")'.format(
                cn=self
            )
        )

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


class ComputeNodeFailureData(namedtuple('_ComputeNodeFailureData', 'dagster_error')):
    def __new__(cls, dagster_error):
        return super(ComputeNodeFailureData, cls).__new__(
            cls,
            dagster_error=check.inst_param(dagster_error, 'dagster_error', DagsterError),
        )


class ComputeNodeResult(
    namedtuple(
        '_ComputeNodeResult',
        'success compute_node tag success_data failure_data',
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
    except DagsterError as de:
        stack_trace = get_formatted_stack_trace(de)
        context.error(str(de), stack_trace=stack_trace)
        raise de
    except Exception as e:  # pylint: disable=W0703
        stack_trace = get_formatted_stack_trace(e)
        context.error(str(e), stack_trace=stack_trace)
        raise_from(
            DagsterUserCodeExecutionError(
                msg.format(**kwargs),
                user_exception=e,
                original_exc_info=sys.exc_info(),
            ),
            e,
        )


class ComputeNodeTag(Enum):
    TRANSFORM = 'TRANSFORM'
    INPUT_EXPECTATION = 'INPUT_EXPECTATION'
    OUTPUT_EXPECTATION = 'OUTPUT_EXPECTATION'
    JOIN = 'JOIN'


EXPECTATION_VALUE_OUTPUT = 'expectation_value'
JOIN_OUTPUT = 'join_output'
EXPECTATION_INPUT = 'expectation_input'


def _yield_transform_results(context, compute_node, conf, inputs):
    gen = compute_node.solid.definition.transform_fn(
        TransformExecutionInfo(context, conf, compute_node.solid.definition),
        inputs,
    )

    if isinstance(gen, Result):
        raise DagsterInvariantViolationError(
            (
                'Transform for solid {solid_name} returned a Result rather than ' +
                'yielding it. The transform_fn of the core SolidDefinition must yield ' +
                'its results'
            ).format(solid_name=compute_node.solid.name)
        )

    if gen is None:
        return

    for result in gen:
        if not isinstance(result, Result):
            raise DagsterInvariantViolationError(
                (
                    'Transform for solid {solid_name} yielded {result} rather an ' +
                    'an instance of the Result class.'
                ).format(
                    result=repr(result),
                    solid_name=compute_node.solid.name,
                )
            )
        yield result


def _collect_result_list(context, compute_node, conf, inputs):
    for result in _yield_transform_results(context, compute_node, conf, inputs):
        context.info(
            'Solid {solid} emitted output "{output}" value {value}'.format(
                solid=compute_node.solid.name,
                output=result.output_name,
                value=repr(result.value),
            )
        )
        yield result


def _execute_core_transform(context, compute_node, conf, inputs):
    '''
    Execute the user-specified transform for the solid. Wrap in an error boundary and do
    all relevant logging and metrics tracking
    '''
    check.inst_param(context, 'context', ExecutionContext)
    check.inst_param(compute_node, 'compute_node', ComputeNode)
    check.dict_param(inputs, 'inputs', key_type=str)

    error_str = 'Error occured during core transform'

    solid = compute_node.solid

    with context.values({'solid': solid.name, 'solid_definition': solid.definition.name}):
        context.debug('Executing core transform for solid {solid}.'.format(solid=solid.name))

        with time_execution_scope() as timer_result, \
            _user_code_error_boundary(context, error_str):

            all_results = list(_collect_result_list(context, compute_node, conf, inputs))

        if len(all_results) != len(solid.definition.output_defs):
            emitted_result_names = set([r.output_name for r in all_results])
            solid_output_names = set(
                [output_def.name for output_def in solid.definition.output_defs]
            )
            omitted_outputs = solid_output_names.difference(emitted_result_names)
            context.info(
                'Solid {solid} did not fire outputs {outputs}'.format(
                    solid=solid.name,
                    outputs=repr(omitted_outputs),
                )
            )

        context.debug(
            'Finished executing transform for solid {solid}. Time elapsed: {millis:.3f} ms'.format(
                solid=compute_node.solid.name,
                millis=timer_result.millis,
            ),
            execution_time_ms=timer_result.millis,
        )

        for result in all_results:
            yield result


class ComputeNodeInput(object):
    def __init__(self, name, dagster_type, prev_output_handle):
        self.name = check.str_param(name, 'name')
        self.dagster_type = check.inst_param(dagster_type, 'dagster_type', DagsterType)
        self.prev_output_handle = check.inst_param(
            prev_output_handle,
            'prev_output_handle',
            ComputeNodeOutputHandle,
        )


class ComputeNodeOutput(object):
    def __init__(self, name, dagster_type):
        self.name = check.str_param(name, 'name')
        self.dagster_type = check.inst_param(dagster_type, 'dagster_type', DagsterType)


class ComputeNode(object):
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
        self.solid = check.inst_param(solid, 'solid', Solid)

    def has_node(self, name):
        check.str_param(name, 'name')
        return name in self._node_output_dict

    def node_named(self, name):
        check.str_param(name, 'name')
        return self._node_output_dict[name]

    def _create_compute_node_result(self, result):
        check.inst_param(result, 'result', Result)

        node_output = self.node_named(result.output_name)

        try:
            evaluation_result = node_output.dagster_type.evaluate_value(result.value)
        except DagsterEvaluateValueError as e:
            raise DagsterInvariantViolationError(
                '''Solid {cn.solid.name} output name {output_name} output {result.value}
                type failure: {error_msg}'''.format(
                    cn=self,
                    result=result,
                    error_msg=','.join(e.args),
                    output_name=result.output_name,
                )
            )

        return ComputeNodeResult.success_result(
            compute_node=self,
            tag=self.tag,
            success_data=ComputeNodeSuccessData(
                output_name=result.output_name,
                value=evaluation_result,
            ),
        )

    def _get_evaluated_input(self, input_name, input_value):
        compute_node_input = self._node_input_dict[input_name]
        try:
            return compute_node_input.dagster_type.evaluate_value(input_value)
        except DagsterEvaluateValueError as evaluate_error:
            raise_from(
                DagsterTypeError(
                    (
                        'Solid {cn.solid.name} input {input_name} received value {input_value} ' +
                        'which does not pass the typecheck for Dagster type ' +
                        '{compute_node_input.dagster_type.name}. Compute node {cn.friendly_name}'
                    ).format(
                        cn=self,
                        input_name=input_name,
                        input_value=input_value,
                        compute_node_input=compute_node_input,
                    )
                ),
                evaluate_error,
            )

    def _compute_result_list(self, context, evaluated_inputs):
        error_str = 'Error occured during compute node {friendly_name}'.format(
            friendly_name=self.friendly_name,
        )

        with _user_code_error_boundary(context, error_str):
            gen = self.compute_fn(context, self, evaluated_inputs)

            if gen is None:
                check.invariant(not self.node_outputs)
                return

            return list(gen)

    def _error_check_results(self, results):
        seen_outputs = set()
        for result in results:
            if not self.has_node(result.output_name):
                output_names = list(
                    [output_def.name for output_def in self.solid.definition.output_defs]
                )
                raise DagsterInvariantViolationError(
                    '''Core transform for {cn.solid.name} returned an output
                    {result.output_name} that does not exist. The available
                    outputs are {output_names}'''
                    .format(cn=self, result=result, output_names=output_names)
                )

            if result.output_name in seen_outputs:
                raise DagsterInvariantViolationError(
                    '''Core transform for {cn.solid.name} returned an output
                    {result.output_name} multiple times'''.format(cn=self, result=result)
                )

            seen_outputs.add(result.output_name)

    def _execute_inner_compute_node_loop(self, context, inputs):
        evaluated_inputs = {}
        # do runtime type checks of inputs versus node inputs
        for input_name, input_value in inputs.items():
            evaluated_inputs[input_name] = self._get_evaluated_input(input_name, input_value)

        results = self._compute_result_list(context, evaluated_inputs)

        self._error_check_results(results)

        return [self._create_compute_node_result(result) for result in results]

    def execute(self, context, inputs):
        check.inst_param(context, 'context', ExecutionContext)
        check.dict_param(inputs, 'inputs', key_type=str)

        try:
            for compute_node_result in self._execute_inner_compute_node_loop(context, inputs):
                yield compute_node_result

        except DagsterError as dagster_error:
            context.error(str(dagster_error))
            yield ComputeNodeResult.failure_result(
                compute_node=self,
                tag=self.tag,
                failure_data=ComputeNodeFailureData(dagster_error=dagster_error, ),
            )
            return

    def output_named(self, name):
        check.str_param(name, 'name')

        for node_output in self.node_outputs:
            if node_output.name == name:
                return node_output

        check.failed('output {name} not found'.format(name=name))


def _all_inputs_covered(cn, results):
    for node_input in cn.node_inputs:
        if node_input.prev_output_handle not in results:
            return False
    return True


def execute_compute_nodes(context, compute_nodes):
    check.inst_param(context, 'context', ExecutionContext)
    check.list_param(compute_nodes, 'compute_nodes', of_type=ComputeNode)

    intermediate_results = {}
    context.debug(
        'Entering execute_compute_nodes loop. Order: {order}'.format(
            order=[cn.friendly_name for cn in compute_nodes]
        )
    )

    for compute_node in compute_nodes:
        if not _all_inputs_covered(compute_node, intermediate_results):
            result_keys = set(intermediate_results.keys())
            expected_outputs = [ni.prev_output_handle for ni in compute_node.node_inputs]

            context.debug(
                'Not all inputs covered for {compute_name}. Not executing.'.
                format(compute_name=compute_node.friendly_name) +
                '\nKeys in result: {result_keys}.'.format(result_keys=result_keys, ) +
                '\nOutputs need for inputs {expected_outputs}'.
                format(expected_outputs=expected_outputs, )
            )
            continue

        input_values = {}
        for node_input in compute_node.node_inputs:
            prev_output_handle = node_input.prev_output_handle
            input_value = intermediate_results[prev_output_handle].success_data.value
            input_values[node_input.name] = input_value

        for result in compute_node.execute(context, input_values):
            check.invariant(isinstance(result, ComputeNodeResult))
            yield result
            output_handle = ComputeNodeOutputHandle(compute_node, result.success_data.output_name)
            intermediate_results[output_handle] = result


def print_graph(graph, printer=print):
    check.inst_param(graph, 'graph', ComputeNodeGraph)
    printer = IndentingPrinter(printer=printer)

    for node in graph.topological_nodes():
        with printer.with_indent('Node {node.friendly_name} Id: {node.guid}'.format(node=node)):
            for node_input in node.node_inputs:
                with printer.with_indent('Input: {node_input.name}'.format(node_input=node_input)):
                    printer.line(
                        'Type: {node_input.dagster_type.name}'.format(node_input=node_input)
                    )
                    printer.line(
                        'From: {node_input.prev_output_handle}'.format(node_input=node_input)
                    )
            for node_output in node.node_outputs:
                with printer.with_indent(
                    'Output: {node_output.name}'.format(node_output=node_output)
                ):
                    printer.line(
                        'Type: {node_output.dagster_type.name}'.format(node_output=node_output)
                    )


class ComputeNodeGraph(object):
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

    check.inst_param(solid, 'solid', Solid)
    check.inst_param(expectation_def, 'input_expct_def', ExpectationDefinition)
    check.inst_param(prev_node_output_handle, 'prev_node_output_handle', ComputeNodeOutputHandle)
    check.inst_param(inout_def, 'inout_def', (InputDefinition, OutputDefinition))

    value_type = inout_def.dagster_type

    return ComputeNode(
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
        compute_fn=_create_expectation_lambda(
            solid,
            inout_def,
            expectation_def,
            EXPECTATION_VALUE_OUTPUT,
        ),
        tag=tag,
        solid=solid,
    )


ComputeNodeSubgraph = namedtuple(
    'ComputeNodeSubgraph',
    'nodes terminal_cn_output_handle',
)


def create_expectations_cn_graph(solid, inout_def, prev_node_output_handle, tag):
    check.inst_param(solid, 'solid', Solid)
    check.inst_param(inout_def, 'inout_def', (InputDefinition, OutputDefinition))
    check.inst_param(prev_node_output_handle, 'prev_node_output_handle', ComputeNodeOutputHandle)
    check.inst_param(tag, 'tag', ComputeNodeTag)

    compute_nodes = []
    input_expect_nodes = []
    for expectation_def in inout_def.expectations:
        expect_compute_node = create_expectation_cn(
            solid=solid,
            expectation_def=expectation_def,
            friendly_name='{solid.name}.{inout_def.name}.expectation.{expectation_def.name}'.format(
                solid=solid, inout_def=inout_def, expectation_def=expectation_def
            ),
            tag=tag,
            prev_node_output_handle=prev_node_output_handle,
            inout_def=inout_def,
        )
        input_expect_nodes.append(expect_compute_node)
        compute_nodes.append(expect_compute_node)

    join_cn = _create_join_node(solid, input_expect_nodes, EXPECTATION_VALUE_OUTPUT)

    output_name = join_cn.node_outputs[0].name
    return ComputeNodeSubgraph(
        compute_nodes + [join_cn],
        ComputeNodeOutputHandle(join_cn, output_name),
    )


class ComputeNodeOutputMap(dict):
    def __getitem__(self, key):
        check.inst_param(key, 'key', SolidOutputHandle)
        return dict.__getitem__(self, key)

    def __setitem__(self, key, val):
        check.inst_param(key, 'key', SolidOutputHandle)
        check.inst_param(val, 'val', ComputeNodeOutputHandle)
        return dict.__setitem__(self, key, val)


def create_conf_value(execution_info, pipeline_solid):
    check.inst_param(execution_info, 'execution_info', ComputeNodeExecutionInfo)
    check.inst_param(pipeline_solid, 'pipeline_solid', Solid)

    solid_def = pipeline_solid.definition

    name = pipeline_solid.name
    solid_configs = execution_info.environment.solids
    config_input = solid_configs[name].config if name in solid_configs else {}

    try:
        return solid_def.config_def.config_type.evaluate_value(config_input)
    except DagsterEvaluateValueError as e:
        raise DagsterTypeError(
            'Error evaluating config for {solid_name}: {error_msg}'.format(
                solid_name=solid_def.name,
                error_msg=','.join(e.args),
            )
        )


def create_compute_node_graph(execution_info):
    check.inst_param(execution_info, 'execution_info', ComputeNodeExecutionInfo)

    execution_graph = execution_info.execution_graph

    dependency_structure = execution_graph.dependency_structure

    compute_nodes = []

    cn_output_node_map = ComputeNodeOutputMap()

    for topo_pipeline_solid in execution_graph.topological_solids:
        cn_inputs = []

        topo_solid = topo_pipeline_solid.definition

        for input_def in topo_solid.input_defs:
            input_handle = topo_pipeline_solid.input_handle(input_def.name)

            check.invariant(
                dependency_structure.has_dep(input_handle),
                '{input_handle} not found in dependency structure'.format(
                    input_handle=input_handle
                ),
            )

            solid_output_handle = dependency_structure.get_dep(input_handle)
            prev_cn_output_handle = cn_output_node_map[solid_output_handle]

            subgraph = create_subgraph_for_input(
                execution_info,
                topo_pipeline_solid,
                prev_cn_output_handle,
                input_def,
            )

            compute_nodes.extend(subgraph.nodes)
            cn_inputs.append(
                ComputeNodeInput(
                    input_def.name,
                    input_def.dagster_type,
                    subgraph.terminal_cn_output_handle,
                )
            )

        conf = create_conf_value(execution_info, topo_pipeline_solid)

        solid_transform_cn = create_compute_node_from_solid_transform(
            topo_pipeline_solid, cn_inputs, conf
        )

        compute_nodes.append(solid_transform_cn)

        for output_def in topo_solid.output_defs:
            subgraph = create_subgraph_for_output(
                execution_info,
                topo_pipeline_solid,
                solid_transform_cn,
                output_def,
            )
            compute_nodes.extend(subgraph.nodes)

            output_handle = topo_pipeline_solid.output_handle(output_def.name)
            cn_output_node_map[output_handle] = subgraph.terminal_cn_output_handle

    return _create_compute_node_graph(compute_nodes)


def _create_compute_node_graph(compute_nodes):
    cn_dict = {}
    for cn in compute_nodes:
        cn_dict[cn.guid] = cn

    deps = defaultdict()

    for cn in compute_nodes:
        deps[cn.guid] = set()
        for cn_input in cn.node_inputs:
            deps[cn.guid].add(cn_input.prev_output_handle.compute_node.guid)

    return ComputeNodeGraph(cn_dict, deps)


def create_subgraph_for_input(execution_info, solid, prev_cn_output_handle, input_def):
    check.inst_param(execution_info, 'execution_info', ComputeNodeExecutionInfo)
    check.inst_param(solid, 'solid', Solid)
    check.inst_param(prev_cn_output_handle, 'prev_cn_output_handle', ComputeNodeOutputHandle)
    check.inst_param(input_def, 'input_def', InputDefinition)

    if execution_info.environment.expectations.evaluate and input_def.expectations:
        return create_expectations_cn_graph(
            solid,
            input_def,
            prev_cn_output_handle,
            tag=ComputeNodeTag.INPUT_EXPECTATION,
        )
    else:
        return ComputeNodeSubgraph(
            nodes=[],
            terminal_cn_output_handle=prev_cn_output_handle,
        )


def create_subgraph_for_output(execution_info, solid, solid_transform_cn, output_def):
    check.inst_param(execution_info, 'execution_info', ComputeNodeExecutionInfo)
    check.inst_param(solid, 'solid', Solid)
    check.inst_param(solid_transform_cn, 'solid_transform_cn', ComputeNode)
    check.inst_param(output_def, 'output_def', OutputDefinition)

    if execution_info.environment.expectations.evaluate and output_def.expectations:
        return create_expectations_cn_graph(
            solid,
            output_def,
            ComputeNodeOutputHandle(solid_transform_cn, output_def.name),
            tag=ComputeNodeTag.OUTPUT_EXPECTATION
        )
    else:
        return ComputeNodeSubgraph(
            nodes=[],
            terminal_cn_output_handle=ComputeNodeOutputHandle(
                solid_transform_cn,
                output_def.name,
            ),
        )


def _create_join_node(solid, prev_nodes, prev_output_name):
    check.inst_param(solid, 'solid', Solid)
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

        output_handle = ComputeNodeOutputHandle(prev_node, prev_output_name)

        node_inputs.append(
            ComputeNodeInput(prev_node.guid, prev_node_output.dagster_type, output_handle)
        )

    return ComputeNode(
        friendly_name='join',
        node_inputs=node_inputs,
        node_outputs=[ComputeNodeOutput(JOIN_OUTPUT, seen_dagster_type)],
        arg_dict={},
        compute_fn=_create_join_lambda,
        tag=ComputeNodeTag.JOIN,
        solid=solid,
    )


def _create_join_lambda(_context, _compute_node, inputs):
    yield Result(output_name=JOIN_OUTPUT, value=list(inputs.values())[0])


def _create_expectation_lambda(solid, inout_def, expectation_def, internal_output_name):
    check.inst_param(solid, 'solid', Solid)
    check.inst_param(inout_def, 'inout_def', (InputDefinition, OutputDefinition))
    check.inst_param(expectation_def, 'expectations_def', ExpectationDefinition)
    check.str_param(internal_output_name, 'internal_output_name')

    def _do_expectation(context, compute_node, inputs):
        with context.values(
            {
                'solid': solid.name,
                inout_def.descriptive_key: inout_def.name,
                'expectation': expectation_def.name
            }
        ):
            value = inputs[EXPECTATION_INPUT]
            info = ExpectationExecutionInfo(context, inout_def, solid, expectation_def)
            expt_result = expectation_def.expectation_fn(info, value)
            if expt_result.success:
                context.debug(
                    'Expectation {friendly_name} succeeded on {value}.'.format(
                        friendly_name=compute_node.friendly_name,
                        value=value,
                    )
                )
                yield Result(output_name=internal_output_name, value=inputs[EXPECTATION_INPUT])
            else:
                context.debug(
                    'Expectation {friendly_name} failed on {value}.'.format(
                        friendly_name=compute_node.friendly_name,
                        value=value,
                    )
                )
                raise DagsterExpectationFailedError(info, value)

    return _do_expectation


def create_compute_node_from_solid_transform(solid, node_inputs, conf):
    check.inst_param(solid, 'solid', Solid)
    check.list_param(node_inputs, 'node_inputs', of_type=ComputeNodeInput)

    return ComputeNode(
        friendly_name='{solid.name}.transform'.format(solid=solid),
        node_inputs=node_inputs,
        node_outputs=[
            ComputeNodeOutput(name=output_def.name, dagster_type=output_def.dagster_type)
            for output_def in solid.definition.output_defs
        ],
        arg_dict={},
        compute_fn=lambda context, compute_node, inputs: _execute_core_transform(
            context,
            compute_node,
            conf,
            inputs,
        ),
        tag=ComputeNodeTag.TRANSFORM,
        solid=solid,
    )
