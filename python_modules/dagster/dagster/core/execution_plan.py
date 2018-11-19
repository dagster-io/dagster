from __future__ import print_function
from collections import (namedtuple, defaultdict)
from contextlib import contextmanager
from enum import Enum
import uuid
import os
import sys

from future.utils import raise_from

import toposort

from dagster import (
    check,
    config,
)

from dagster.utils.indenting_printer import IndentingPrinter
from dagster.utils.logging import get_formatted_stack_trace

from dagster.utils.timing import time_execution_scope

from .definitions import (
    ExecutionGraph,
    ExpectationDefinition,
    ExpectationExecutionInfo,
    InputDefinition,
    OutputDefinition,
    Result,
    SolidOutputHandle,
    Solid,
    TransformExecutionInfo,
)

from .evaluator import throwing_evaluate_config_value

from .execution_context import (
    ExecutionContext,
)

from .errors import (
    DagsterError,
    DagsterEvaluateConfigValueError,
    DagsterExpectationFailedError,
    DagsterInvariantViolationError,
    DagsterRuntimeCoercionError,
    DagsterTypeError,
    DagsterUserCodeExecutionError,
)

from .types import DagsterType


class ExecutionPlanInfo(namedtuple('_ExecutionPlanInfo', 'context execution_graph environment')):
    def __new__(cls, context, execution_graph, environment):
        return super(ExecutionPlanInfo, cls).__new__(
            cls,
            check.inst_param(context, 'context', ExecutionContext),
            check.inst_param(execution_graph, 'execution_graph', ExecutionGraph),
            check.inst_param(environment, 'environment', config.Environment),
        )

    @property
    def pipeline(self):
        return self.execution_graph.pipeline

    @property
    def serialize_intermediates(self):
        return self.environment.execution.serialize_intermediates


class StepOutputHandle(namedtuple('_StepOutputHandle', 'step output_name')):
    def __new__(cls, step, output_name):
        return super(StepOutputHandle, cls).__new__(
            cls,
            step=check.inst_param(step, 'step', ExecutionStep),
            output_name=check.str_param(output_name, 'output_name'),
        )

    # Make this hashable so it be a key in a dictionary

    def __str__(self):
        return (
            'StepOutputHandle'
            '(step="{step.friendly_name}", output_name="{output_name}")'.format(
                step=self.step,
                output_name=self.output_name,
            )
        )

    def __repr__(self):
        return (
            'StepOutputHandle'
            '(step="{step.friendly_name}", output_name="{output_name}")'.format(
                step=self.step,
                output_name=self.output_name,
            )
        )

    def __hash__(self):
        return hash(self.step.guid + self.output_name)

    def __eq__(self, other):
        return self.step.guid == other.step.guid and self.output_name == other.output_name


class StepSuccessData(namedtuple('_StepSuccessData', 'output_name value')):
    def __new__(cls, output_name, value):
        return super(StepSuccessData, cls).__new__(
            cls,
            output_name=check.str_param(output_name, 'output_name'),
            value=value,
        )


class StepFailureData(namedtuple('_StepFailureData', 'dagster_error')):
    def __new__(cls, dagster_error):
        return super(StepFailureData, cls).__new__(
            cls,
            dagster_error=check.inst_param(dagster_error, 'dagster_error', DagsterError),
        )


class StepResult(namedtuple(
    '_StepResult',
    'success step tag success_data failure_data',
)):
    @staticmethod
    def success_result(step, tag, success_data):
        return StepResult(
            success=True,
            step=check.inst_param(step, 'step', ExecutionStep),
            tag=check.inst_param(tag, 'tag', StepTag),
            success_data=check.inst_param(success_data, 'success_data', StepSuccessData),
            failure_data=None,
        )

    @staticmethod
    def failure_result(step, tag, failure_data):
        return StepResult(
            success=False,
            step=check.inst_param(step, 'step', ExecutionStep),
            tag=check.inst_param(tag, 'tag', StepTag),
            success_data=None,
            failure_data=check.inst_param(failure_data, 'failure_data', StepFailureData),
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


class StepTag(Enum):
    TRANSFORM = 'TRANSFORM'
    INPUT_EXPECTATION = 'INPUT_EXPECTATION'
    OUTPUT_EXPECTATION = 'OUTPUT_EXPECTATION'
    JOIN = 'JOIN'
    SERIALIZE = 'SERIALIZE'


EXPECTATION_VALUE_OUTPUT = 'expectation_value'
JOIN_OUTPUT = 'join_output'
EXPECTATION_INPUT = 'expectation_input'


def _yield_transform_results(context, step, conf, inputs):
    gen = step.solid.definition.transform_fn(
        TransformExecutionInfo(context, conf, step.solid.definition),
        inputs,
    )

    if isinstance(gen, Result):
        raise DagsterInvariantViolationError(
            (
                'Transform for solid {solid_name} returned a Result rather than ' +
                'yielding it. The transform_fn of the core SolidDefinition must yield ' +
                'its results'
            ).format(solid_name=step.solid.name)
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
                    solid_name=step.solid.name,
                )
            )

        context.info(
            'Solid {solid} emitted output "{output}" value {value}'.format(
                solid=step.solid.name,
                output=result.output_name,
                value=repr(result.value),
            )
        )
        yield result


def _execute_core_transform(context, step, conf, inputs):
    '''
    Execute the user-specified transform for the solid. Wrap in an error boundary and do
    all relevant logging and metrics tracking
    '''
    check.inst_param(context, 'context', ExecutionContext)
    check.inst_param(step, 'step', ExecutionStep)
    check.dict_param(inputs, 'inputs', key_type=str)

    error_str = 'Error occured during core transform'

    solid = step.solid

    with context.values({'solid': solid.name, 'solid_definition': solid.definition.name}):
        context.debug('Executing core transform for solid {solid}.'.format(solid=solid.name))

        with time_execution_scope() as timer_result, \
            _user_code_error_boundary(context, error_str):

            all_results = list(_yield_transform_results(context, step, conf, inputs))

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
                solid=step.solid.name,
                millis=timer_result.millis,
            ),
            execution_time_ms=timer_result.millis,
        )

        for result in all_results:
            yield result


class StepInput(object):
    def __init__(self, name, dagster_type, prev_output_handle):
        self.name = check.str_param(name, 'name')
        self.dagster_type = check.inst_param(dagster_type, 'dagster_type', DagsterType)
        self.prev_output_handle = check.inst_param(
            prev_output_handle,
            'prev_output_handle',
            StepOutputHandle,
        )


class StepOutput(object):
    def __init__(self, name, dagster_type):
        self.name = check.str_param(name, 'name')
        self.dagster_type = check.inst_param(dagster_type, 'dagster_type', DagsterType)


class ExecutionStep(object):
    def __init__(self, friendly_name, step_inputs, step_outputs, compute_fn, tag, solid):
        self.guid = str(uuid.uuid4())
        self.friendly_name = check.str_param(friendly_name, 'friendly_name')

        self.step_inputs = check.list_param(step_inputs, 'step_inputs', of_type=StepInput)
        self._step_input_dict = {si.name: si for si in step_inputs}

        self.step_outputs = check.list_param(step_outputs, 'step_outputs', of_type=StepOutput)
        self._step_output_dict = {so.name: so for so in step_outputs}

        self.compute_fn = check.callable_param(compute_fn, 'compute_fn')
        self.tag = check.inst_param(tag, 'tag', StepTag)
        self.solid = check.inst_param(solid, 'solid', Solid)

    def has_step(self, name):
        check.str_param(name, 'name')
        return name in self._step_output_dict

    def step_named(self, name):
        check.str_param(name, 'name')
        return self._step_output_dict[name]

    def _create_step_result(self, result):
        check.inst_param(result, 'result', Result)

        step_output = self.step_named(result.output_name)

        try:
            coerced_value = step_output.dagster_type.coerce_runtime_value(result.value)
        except DagsterRuntimeCoercionError as e:
            raise DagsterInvariantViolationError(
                '''Solid {step.solid.name} output name {output_name} output {result.value}
                type failure: {error_msg}'''.format(
                    step=self,
                    result=result,
                    error_msg=','.join(e.args),
                    output_name=result.output_name,
                )
            )

        return StepResult.success_result(
            step=self,
            tag=self.tag,
            success_data=StepSuccessData(
                output_name=result.output_name,
                value=coerced_value,
            ),
        )

    def _get_evaluated_input(self, input_name, input_value):
        step_input = self._step_input_dict[input_name]
        try:
            return step_input.dagster_type.coerce_runtime_value(input_value)
        except DagsterRuntimeCoercionError as evaluate_error:
            raise_from(
                DagsterTypeError(
                    (
                        'Solid {step.solid.name} input {input_name} received value {input_value} ' +
                        'which does not pass the typecheck for Dagster type ' +
                        '{step_input.dagster_type.name}. Step {step.friendly_name}'
                    ).format(
                        step=self,
                        input_name=input_name,
                        input_value=input_value,
                        step_input=step_input,
                    )
                ),
                evaluate_error,
            )

    def _compute_result_list(self, context, evaluated_inputs):
        error_str = 'Error occured during step {friendly_name}'.format(
            friendly_name=self.friendly_name,
        )

        with _user_code_error_boundary(context, error_str):
            gen = self.compute_fn(context, self, evaluated_inputs)

            if gen is None:
                check.invariant(not self.step_outputs)
                return

            return list(gen)

    def _error_check_results(self, results):
        seen_outputs = set()
        for result in results:
            if not self.has_step(result.output_name):
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

    def _execute_steps_core_loop(self, context, inputs):
        evaluated_inputs = {}
        # do runtime type checks of inputs versus step inputs
        for input_name, input_value in inputs.items():
            evaluated_inputs[input_name] = self._get_evaluated_input(input_name, input_value)

        results = self._compute_result_list(context, evaluated_inputs)

        self._error_check_results(results)

        return [self._create_step_result(result) for result in results]

    def execute(self, context, inputs):
        check.inst_param(context, 'context', ExecutionContext)
        check.dict_param(inputs, 'inputs', key_type=str)

        try:
            for step_result in self._execute_steps_core_loop(context, inputs):
                yield step_result

        except DagsterError as dagster_error:
            context.error(str(dagster_error))
            yield StepResult.failure_result(
                step=self,
                tag=self.tag,
                failure_data=StepFailureData(dagster_error=dagster_error, ),
            )
            return

    def output_named(self, name):
        check.str_param(name, 'name')

        for step_output in self.step_outputs:
            if step_output.name == name:
                return step_output

        check.failed('output {name} not found'.format(name=name))


def _all_inputs_covered(cn, results):
    for step_input in cn.step_inputs:
        if step_input.prev_output_handle not in results:
            return False
    return True


def execute_steps(context, steps):
    check.inst_param(context, 'context', ExecutionContext)
    check.list_param(steps, 'steps', of_type=ExecutionStep)

    intermediate_results = {}
    context.debug(
        'Entering execute_steps loop. Order: {order}'.format(
            order=[cn.friendly_name for cn in steps]
        )
    )

    for step in steps:
        if not _all_inputs_covered(step, intermediate_results):
            result_keys = set(intermediate_results.keys())
            expected_outputs = [ni.prev_output_handle for ni in step.step_inputs]

            context.debug(
                'Not all inputs covered for {step}. Not executing.'.format(step=step.friendly_name)
                + '\nKeys in result: {result_keys}.'.format(result_keys=result_keys) +
                '\nOutputs need for inputs {expected_outputs}'.
                format(expected_outputs=expected_outputs, )
            )
            continue

        input_values = {}
        for step_input in step.step_inputs:
            prev_output_handle = step_input.prev_output_handle
            input_value = intermediate_results[prev_output_handle].success_data.value
            input_values[step_input.name] = input_value

        for result in step.execute(context, input_values):
            check.invariant(isinstance(result, StepResult))
            yield result
            output_handle = StepOutputHandle(step, result.success_data.output_name)
            intermediate_results[output_handle] = result


def print_graph(graph, printer=print):
    check.inst_param(graph, 'graph', ExecutionPlan)
    printer = IndentingPrinter(printer=printer)

    for step in graph.topological_steps():
        with printer.with_indent('Step {step.friendly_name} Id: {step.guid}'.format(step=step)):
            for step_input in step.step_inputs:
                with printer.with_indent('Input: {step_input.name}'.format(step_input=step_input)):
                    printer.line(
                        'Type: {step_input.dagster_type.name}'.format(step_input=step_input)
                    )
                    printer.line(
                        'From: {step_input.prev_output_handle}'.format(step_input=step_input)
                    )

            for step_output in step.step_outputs:
                with printer.with_indent(
                    'Output: {step_output.name}'.format(step_output=step_output)
                ):
                    printer.line(
                        'Type: {step_output.dagster_type.name}'.format(step_output=step_output)
                    )


class ExecutionPlan(object):
    def __init__(self, step_dict, deps):
        self.step_dict = check.dict_param(
            step_dict,
            'step_dict',
            key_type=str,
            value_type=ExecutionStep,
        )
        self.deps = check.dict_param(deps, 'deps', key_type=str, value_type=set)
        self.steps = list(step_dict.values())

    def topological_steps(self):
        sorted_step_guids = toposort.toposort_flatten(self.deps)
        for step_guid in sorted_step_guids:
            yield self.step_dict[step_guid]


def create_expectation_step(
    solid,
    expectation_def,
    friendly_name,
    tag,
    prev_step_output_handle,
    inout_def,
):

    check.inst_param(solid, 'solid', Solid)
    check.inst_param(expectation_def, 'input_expct_def', ExpectationDefinition)
    check.inst_param(prev_step_output_handle, 'prev_step_output_handle', StepOutputHandle)
    check.inst_param(inout_def, 'inout_def', (InputDefinition, OutputDefinition))

    value_type = inout_def.dagster_type

    return ExecutionStep(
        friendly_name=friendly_name,
        step_inputs=[
            StepInput(
                name=EXPECTATION_INPUT,
                dagster_type=value_type,
                prev_output_handle=prev_step_output_handle,
            )
        ],
        step_outputs=[
            StepOutput(name=EXPECTATION_VALUE_OUTPUT, dagster_type=value_type),
        ],
        compute_fn=_create_expectation_lambda(
            solid,
            inout_def,
            expectation_def,
            EXPECTATION_VALUE_OUTPUT,
        ),
        tag=tag,
        solid=solid,
    )


ExecutionSubPlan = namedtuple(
    'ExecutionSubPlan',
    'steps terminal_step_output_handle',
)


def create_expectations_subplan(solid, inout_def, prev_step_output_handle, tag):
    check.inst_param(solid, 'solid', Solid)
    check.inst_param(inout_def, 'inout_def', (InputDefinition, OutputDefinition))
    check.inst_param(prev_step_output_handle, 'prev_step_output_handle', StepOutputHandle)
    check.inst_param(tag, 'tag', StepTag)

    steps = []
    input_expect_steps = []
    for expectation_def in inout_def.expectations:
        expect_step = create_expectation_step(
            solid=solid,
            expectation_def=expectation_def,
            friendly_name='{solid.name}.{inout_def.name}.expectation.{expectation_def.name}'.format(
                solid=solid, inout_def=inout_def, expectation_def=expectation_def
            ),
            tag=tag,
            prev_step_output_handle=prev_step_output_handle,
            inout_def=inout_def,
        )
        input_expect_steps.append(expect_step)
        steps.append(expect_step)

    join_step = _create_join_step(solid, input_expect_steps, EXPECTATION_VALUE_OUTPUT)

    output_name = join_step.step_outputs[0].name
    return ExecutionSubPlan(
        steps + [join_step],
        StepOutputHandle(join_step, output_name),
    )


class StepOutputMap(dict):
    def __getitem__(self, key):
        check.inst_param(key, 'key', SolidOutputHandle)
        return dict.__getitem__(self, key)

    def __setitem__(self, key, val):
        check.inst_param(key, 'key', SolidOutputHandle)
        check.inst_param(val, 'val', StepOutputHandle)
        return dict.__setitem__(self, key, val)


def create_config_value(execution_info, pipeline_solid):
    check.inst_param(execution_info, 'execution_info', ExecutionPlanInfo)
    check.inst_param(pipeline_solid, 'pipeline_solid', Solid)

    solid_def = pipeline_solid.definition

    name = pipeline_solid.name
    solid_configs = execution_info.environment.solids
    config_input = solid_configs[name].config if name in solid_configs else None

    if solid_def.config_def is None:
        if config_input is not None:
            raise DagsterInvariantViolationError(
                (
                    'Solid {solid} was provided {config_input} but does not take config'.format(
                        solid=solid_def.name,
                        config_input=repr(config_input),
                    )
                )
            )
        return None

    try:
        return throwing_evaluate_config_value(solid_def.config_def.config_type, config_input)
    except DagsterEvaluateConfigValueError as eval_error:
        raise_from(
            DagsterTypeError(
                'Error evaluating config for {solid_name}: {error_msg}'.format(
                    solid_name=solid_def.name,
                    error_msg=','.join(eval_error.args),
                )
            ),
            eval_error,
        )


# This is the state that is built up during the execution plan build process.
# steps is just a list of the steps that have been created
# step_output_map maps logical solid outputs (solid_name, output_name) to particular
# step outputs. This covers the case where a solid maps to multiple steps
# and one wants to be able to attach to the logical output of a solid during execution
StepBuilderState = namedtuple('StepBuilderState', 'steps step_output_map')


def create_step_inputs(info, state, pipeline_solid):
    check.inst_param(info, 'info', ExecutionPlanInfo)
    check.inst_param(state, 'state', StepBuilderState)
    check.inst_param(pipeline_solid, 'pipeline_solid', Solid)

    step_inputs = []

    topo_solid = pipeline_solid.definition
    dependency_structure = info.execution_graph.dependency_structure

    for input_def in topo_solid.input_defs:
        input_handle = pipeline_solid.input_handle(input_def.name)

        check.invariant(
            dependency_structure.has_dep(input_handle),
            '{input_handle} not found in dependency structure'.format(input_handle=input_handle),
        )

        solid_output_handle = dependency_structure.get_dep(input_handle)
        prev_step_output_handle = state.step_output_map[solid_output_handle]

        subgraph = create_subgraph_for_input(
            info,
            pipeline_solid,
            prev_step_output_handle,
            input_def,
        )

        state.steps.extend(subgraph.steps)
        step_inputs.append(
            StepInput(
                input_def.name,
                input_def.dagster_type,
                subgraph.terminal_step_output_handle,
            )
        )

    return step_inputs


def create_execution_plan_core(execution_info):
    check.inst_param(execution_info, 'execution_info', ExecutionPlanInfo)

    execution_graph = execution_info.execution_graph

    state = StepBuilderState(
        steps=[],
        step_output_map=StepOutputMap(),
    )

    for pipeline_solid in execution_graph.topological_solids:
        step_inputs = create_step_inputs(execution_info, state, pipeline_solid)

        solid_transform_step = create_transform_step(
            pipeline_solid,
            step_inputs,
            create_config_value(execution_info, pipeline_solid),
        )

        state.steps.append(solid_transform_step)

        for output_def in pipeline_solid.definition.output_defs:
            subgraph = create_subplan_for_output(
                execution_info,
                pipeline_solid,
                solid_transform_step,
                output_def,
            )
            state.steps.extend(subgraph.steps)

            output_handle = pipeline_solid.output_handle(output_def.name)
            state.step_output_map[output_handle] = subgraph.terminal_step_output_handle

    return _create_execution_plan(state.steps)


def _create_execution_plan(steps):
    check.list_param(steps, 'steps', of_type=ExecutionStep)

    step_dict = {step.guid: step for step in steps}

    deps = defaultdict()

    for step in steps:
        deps[step.guid] = set()
        for step_input in step.step_inputs:
            deps[step.guid].add(step_input.prev_output_handle.step.guid)

    return ExecutionPlan(step_dict, deps)


def create_subgraph_for_input(execution_info, solid, prev_step_output_handle, input_def):
    check.inst_param(execution_info, 'execution_info', ExecutionPlanInfo)
    check.inst_param(solid, 'solid', Solid)
    check.inst_param(prev_step_output_handle, 'prev_step_output_handle', StepOutputHandle)
    check.inst_param(input_def, 'input_def', InputDefinition)

    if execution_info.environment.expectations.evaluate and input_def.expectations:
        return create_expectations_subplan(
            solid,
            input_def,
            prev_step_output_handle,
            tag=StepTag.INPUT_EXPECTATION,
        )
    else:
        return ExecutionSubPlan(
            steps=[],
            terminal_step_output_handle=prev_step_output_handle,
        )


SERIALIZE_INPUT = 'serialize_input'
SERIALIZE_OUTPUT = 'serialize_output'


def _decorate_with_expectations(execution_info, solid, transform_step, output_def):
    check.inst_param(execution_info, 'execution_info', ExecutionPlanInfo)
    check.inst_param(solid, 'solid', Solid)
    check.inst_param(transform_step, 'transform_step', ExecutionStep)
    check.inst_param(output_def, 'output_def', OutputDefinition)

    if execution_info.environment.expectations.evaluate and output_def.expectations:
        return create_expectations_subplan(
            solid,
            output_def,
            StepOutputHandle(transform_step, output_def.name),
            tag=StepTag.OUTPUT_EXPECTATION
        )
    else:
        return ExecutionSubPlan(
            steps=[],
            terminal_step_output_handle=StepOutputHandle(
                transform_step,
                output_def.name,
            ),
        )


def _decorate_with_serialization(execution_info, solid, output_def, subplan):
    check.inst_param(execution_info, 'execution_info', ExecutionPlanInfo)
    check.inst_param(solid, 'solid', Solid)
    check.inst_param(output_def, 'output_def', OutputDefinition)
    check.inst_param(subplan, 'subplan', ExecutionSubPlan)

    if execution_info.serialize_intermediates:
        serialize_step = _create_serialization_step(solid, output_def, subplan)
        return ExecutionSubPlan(
            steps=subplan.steps + [serialize_step],
            terminal_step_output_handle=StepOutputHandle(
                serialize_step,
                SERIALIZE_OUTPUT,
            )
        )
    else:
        return subplan


def create_subplan_for_output(execution_info, solid, solid_transform_cn, output_def):
    check.inst_param(execution_info, 'execution_info', ExecutionPlanInfo)
    check.inst_param(solid, 'solid', Solid)
    check.inst_param(solid_transform_cn, 'solid_transform_cn', ExecutionStep)
    check.inst_param(output_def, 'output_def', OutputDefinition)

    subgraph = _decorate_with_expectations(execution_info, solid, solid_transform_cn, output_def)

    return _decorate_with_serialization(execution_info, solid, output_def, subgraph)


def _create_serialization_lambda(solid, output_def):
    check.inst_param(solid, 'solid', Solid)
    check.inst_param(output_def, 'output_def', OutputDefinition)

    def fn(context, _step, inputs):
        value = inputs[SERIALIZE_INPUT]
        path = '/tmp/dagster/runs/{run_id}/{solid_name}/outputs/{output_name}'.format(
            run_id=context.run_id,
            solid_name=solid.name,
            output_name=output_def.name,
        )

        if not os.path.exists(path):
            os.makedirs(path)

        output_def.dagster_type.serialize_value(path, value)

        context.info('Serialized output to {path}'.format(path=path))

        yield Result(value, SERIALIZE_OUTPUT)

    return fn


def _create_serialization_step(solid, output_def, prev_subgraph):
    check.inst_param(solid, 'solid', Solid)
    check.inst_param(output_def, 'output_def', OutputDefinition)
    check.inst_param(prev_subgraph, 'prev_subgraph', ExecutionSubPlan)

    return ExecutionStep(
        friendly_name='serialize.' + solid.name + '.' + output_def.name,
        step_inputs=[
            StepInput(
                name=SERIALIZE_INPUT,
                dagster_type=output_def.dagster_type,
                prev_output_handle=prev_subgraph.terminal_step_output_handle,
            )
        ],
        step_outputs=[StepOutput(
            name=SERIALIZE_OUTPUT,
            dagster_type=output_def.dagster_type,
        )],
        compute_fn=_create_serialization_lambda(solid, output_def),
        tag=StepTag.SERIALIZE,
        solid=solid,
    )


def _create_join_step(solid, prev_steps, prev_output_name):
    check.inst_param(solid, 'solid', Solid)
    check.list_param(prev_steps, 'prev_steps', of_type=ExecutionStep)
    check.invariant(len(prev_steps) > 0)
    check.str_param(prev_output_name, 'output_name')

    step_inputs = []
    seen_dagster_type = None
    for prev_step in prev_steps:
        prev_step_output = prev_step.output_named(prev_output_name)

        if seen_dagster_type is None:
            seen_dagster_type = prev_step_output.dagster_type
        else:
            check.invariant(seen_dagster_type == prev_step_output.dagster_type)

        output_handle = StepOutputHandle(prev_step, prev_output_name)

        step_inputs.append(StepInput(prev_step.guid, prev_step_output.dagster_type, output_handle))

    return ExecutionStep(
        friendly_name='join',
        step_inputs=step_inputs,
        step_outputs=[StepOutput(JOIN_OUTPUT, seen_dagster_type)],
        compute_fn=_create_join_lambda,
        tag=StepTag.JOIN,
        solid=solid,
    )


def _create_join_lambda(_context, _step, inputs):
    yield Result(output_name=JOIN_OUTPUT, value=list(inputs.values())[0])


def _create_expectation_lambda(solid, inout_def, expectation_def, internal_output_name):
    check.inst_param(solid, 'solid', Solid)
    check.inst_param(inout_def, 'inout_def', (InputDefinition, OutputDefinition))
    check.inst_param(expectation_def, 'expectations_def', ExpectationDefinition)
    check.str_param(internal_output_name, 'internal_output_name')

    def _do_expectation(context, step, inputs):
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
                        friendly_name=step.friendly_name,
                        value=value,
                    )
                )
                yield Result(output_name=internal_output_name, value=inputs[EXPECTATION_INPUT])
            else:
                context.debug(
                    'Expectation {friendly_name} failed on {value}.'.format(
                        friendly_name=step.friendly_name,
                        value=value,
                    )
                )
                raise DagsterExpectationFailedError(info, value)

    return _do_expectation


def create_transform_step(solid, step_inputs, conf):
    check.inst_param(solid, 'solid', Solid)
    check.list_param(step_inputs, 'step_inputs', of_type=StepInput)

    return ExecutionStep(
        friendly_name='{solid.name}.transform'.format(solid=solid),
        step_inputs=step_inputs,
        step_outputs=[
            StepOutput(name=output_def.name, dagster_type=output_def.dagster_type)
            for output_def in solid.definition.output_defs
        ],
        compute_fn=lambda context, step, inputs: _execute_core_transform(
            context,
            step,
            conf,
            inputs,
        ),
        tag=StepTag.TRANSFORM,
        solid=solid,
    )
