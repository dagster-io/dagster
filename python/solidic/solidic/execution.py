from collections import (namedtuple, OrderedDict)
from contextlib import contextmanager
import copy
from enum import Enum

import check

from solidic_utils.logging import (CompositeLogger, ERROR)
from solidic_utils.timing import time_execution_scope

from .definitions import (
    Solid,
    SolidInputDefinition,
    SolidOutputTypeDefinition,
    SolidExpectationDefinition,
    SolidExpectationResult,
)

from .graph import SolidPipeline


class SolidExecutionFailureReason(Enum):
    USER_CODE_ERROR = 'USER_CODE_ERROR'
    FRAMEWORK_ERROR = 'FRAMEWORK_ERROR'
    EXPECTATION_FAILURE = 'EXPECATION_FAILURE'


class SolidError(Exception):
    pass


class SolidTypeError(SolidError):
    '''Indicates an error in the solid type system (e.g. mismatched arguments)'''
    pass


class SolidExecutionError(SolidError):
    '''Indicates an error in user space code'''
    pass


class SolidExecutionContext:
    def __init__(self, loggers=None, log_level=ERROR):
        self._logger = CompositeLogger(loggers=loggers, level=log_level)
        self._context_dict = OrderedDict()

    def _maybe_quote(self, val):
        str_val = str(val)
        if ' ' in str_val:
            return '"{val}"'.format(val=str_val)
        return str_val

    def _log(self, method, msg, frmtargs):
        check.str_param(method, 'method')
        check.str_param(msg, 'msg')
        check.dict_param(frmtargs, 'frmtargs')

        kv_message = ' '.join(
            [
                '{key}={value}'.format(key=key, value=self._maybe_quote(value))
                for key, value in self._context_dict.items()
            ]
        )

        full_message = 'message="{message}" {kv_message}'.format(
            message=msg.format(**frmtargs), kv_message=kv_message
        )
        getattr(self._logger, method)(full_message, extra=self._context_dict)

    def debug(self, msg, **frmtargs):
        return self._log('debug', msg, frmtargs)

    def info(self, msg, **frmtargs):
        return self._log('info', msg, frmtargs)

    def warn(self, msg, **frmtargs):
        return self._log('warn', msg, frmtargs)

    def error(self, msg, **frmtargs):
        return self._log('error', msg, frmtargs)

    def critical(self, msg, **frmtargs):
        return self._log('critical', msg, frmtargs)

    @contextmanager
    def value(self, key, value):
        check.str_param(key, 'key')
        check.not_none_param(value, 'value')

        check.invariant(not key in self._context_dict, 'Should not be in context')

        self._context_dict[key] = value

        yield

        self._context_dict.pop(key)


class SolidExecutionResult:
    def __init__(
        self,
        success,
        solid,
        materialized_output,
        reason=None,
        exception=None,
        failed_expectation_results=None
    ):
        self.success = check.bool_param(success, 'success')
        if not success:
            check.param_invariant(
                isinstance(reason, SolidExecutionFailureReason), 'reason',
                'Must provide a reason is result is a failure'
            )
        self.materialized_output = materialized_output
        self.solid = check.inst_param(solid, 'solid', Solid)
        self.reason = reason
        self.exception = check.opt_inst_param(exception, 'exception', Exception)
        self.failed_expectation_results = check.opt_list_param(
            failed_expectation_results, 'failed_expectation_result', of_type=SolidExpectationResult
        )

    @property
    def name(self):
        return self.solid.name


@contextmanager
def user_code_error_boundary(msg, **kwargs):
    try:
        yield
    except Exception as e:
        raise SolidExecutionError(msg.format(**kwargs), e)


def materialize_input(context, input_definition, arg_dict):
    check.inst_param(context, 'context', SolidExecutionContext)
    check.inst_param(input_definition, 'input_defintion', SolidInputDefinition)
    check.dict_param(arg_dict, 'arg_dict', key_type=str)

    with context.value('input', input_definition.name), context.value('arg_dict', arg_dict):
        expected_args = set(input_definition.argument_def_dict.keys())
        received_args = set(arg_dict.keys())
        if expected_args != received_args:
            raise SolidTypeError(
                'Argument mismatch in input {input_name}. Expected {expected} got {received}'.
                format(
                    input_name=input_definition.name,
                    expected=repr(expected_args),
                    received=repr(received_args),
                )
            )

        for arg_name, arg_value in arg_dict.items():
            arg_def_type = input_definition.argument_def_dict[arg_name]
            if not arg_def_type.is_python_valid_value(arg_value):
                raise SolidTypeError(
                    'Expected type {typename} for arg {arg_name} for {input_name} but got {arg_value}'.
                    format(
                        typename=arg_def_type.name,
                        arg_name=arg_name,
                        input_name=input_definition.name,
                        arg_value=repr(arg_value),
                    )
                )

        error_str = 'Error occured while loading input "{input_name}"'
        with user_code_error_boundary(error_str, input_name=input_definition.name):
            context.info('Entering input implementation')

            materialized_input = input_definition.input_fn(context, arg_dict)

            return materialized_input


def execute_input_expectation(context, expectation_def, materialized_input):
    check.inst_param(context, 'context', SolidExecutionContext)
    check.inst_param(expectation_def, 'expectation_def', SolidExpectationDefinition)

    error_str = 'Error occured while evaluation expectation "{expectation_name}" in input'
    with user_code_error_boundary(error_str, expectation_name=expectation_def.name):
        expectation_result = expectation_def.expectation_fn(materialized_input)

    if not isinstance(expectation_result, SolidExpectationResult):
        raise SolidExecutionError('Must return SolidExpectationResult from expectation function')

    return expectation_result


def execute_output_expectation(context, expectation_def, materialized_output):
    check.inst_param(context, 'context', SolidExecutionContext)
    check.inst_param(expectation_def, 'expectation_def', SolidExpectationDefinition)

    error_str = 'Error occured while evaluation expectation "{expectation_name}" in output'
    with user_code_error_boundary(error_str, expectation_name=expectation_def.name):
        expectation_result = expectation_def.expectation_fn(materialized_output)

    if not isinstance(expectation_result, SolidExpectationResult):
        raise SolidExecutionError('Must return SolidExpectationResult from expectation function')

    return expectation_result


def execute_core_transform(context, solid_transform_fn, materialized_inputs):
    check.inst_param(context, 'context', SolidExecutionContext)
    check.callable_param(solid_transform_fn, 'solid_transform_fn')
    check.dict_param(materialized_inputs, 'materialized_inputs', key_type=str)

    error_str = 'Error occured during core transform'
    with user_code_error_boundary(error_str):
        with time_execution_scope() as timer_result:
            materialized_output = solid_transform_fn(**materialized_inputs)

        context.info('Core transform took {millis:.3f} ms', millis=timer_result.millis)

        check.invariant(
            not isinstance(materialized_output, SolidExecutionResult),
            'Tricksy hobbitess cannot return an execution result from the transform ' + \
            'function in order to fool the framework'
        )

        return materialized_output


def execute_output(context, output_type_def, output_arg_dict, materialized_output):
    check.inst_param(context, 'context', SolidExecutionContext)
    check.inst_param(output_type_def, 'output_type_def', SolidOutputTypeDefinition)
    check.dict_param(output_arg_dict, 'output_arg_dict', key_type=str)

    expected_args = set(output_type_def.argument_def_dict.keys())
    received_args = set(output_arg_dict.keys())

    if expected_args != received_args:
        raise SolidTypeError(
            'Argument mismatch in output. Expected {expected} got {received}'.format(
                expected=repr(expected_args),
                received=repr(received_args),
            )
        )

    for arg_name, arg_value in output_arg_dict.items():
        arg_def_type = output_type_def.argument_def_dict[arg_name]
        if not arg_def_type.is_python_valid_value(arg_value):
            raise SolidTypeError(
                'Expected type {typename} for arg {arg_name} in output but got {arg_value}'.format(
                    typename=arg_def_type.name,
                    arg_name=arg_name,
                    arg_value=repr(arg_value),
                )
            )

    error_str = 'Error during execution of output'
    with user_code_error_boundary(error_str):
        context.info('Entering output implementation')
        output_type_def.output_fn(materialized_output, context, output_arg_dict)


SolidInputExpectationRunResults = namedtuple(
    'SolidInputExpectationRunResults', 'input_name passes fails'
)


class SolidAllInputExpectationsRunResults:
    def __init__(self, run_results_list):
        self.run_results_list = check.list_param(
            run_results_list, 'run_results_list', of_type=SolidInputExpectationRunResults
        )

        all_passes = []
        all_fails = []
        for run_results in run_results_list:
            all_passes.extend(run_results.passes)
            all_fails.extend(run_results.fails)

        self.all_passes = all_passes
        self.all_fails = all_fails

    @property
    def success(self):
        return not self.all_fails


def execute_all_input_expectations(context, solid, materialized_inputs):
    check.inst_param(context, 'context', SolidExecutionContext)
    check.dict_param(materialized_inputs, 'materialized_inputs', key_type=str)

    run_results_list = []

    for input_name in materialized_inputs.keys():
        input_def = solid.input_def_named(input_name)
        materialized_input = materialized_inputs[input_name]

        passes = []
        fails = []

        for input_expectation_def in input_def.expectations:
            input_expectation_result = execute_input_expectation(
                context, input_expectation_def, materialized_input
            )

            if input_expectation_result.success:
                passes.append(input_expectation_result)
            else:
                fails.append(input_expectation_result)

        run_results_list.append(
            SolidInputExpectationRunResults(input_name=input_name, passes=passes, fails=fails)
        )

    return SolidAllInputExpectationsRunResults(run_results_list)


def materialize_all_inputs(context, solid, input_arg_dicts):
    check.inst_param(context, 'context', SolidExecutionContext)

    materialized_inputs = {}

    for input_name, arg_dict in input_arg_dicts.items():
        input_def = solid.input_def_named(input_name)
        materialized_input = materialize_input(context, input_def, arg_dict)
        materialized_inputs[input_name] = materialized_input

    return materialized_inputs


def pipeline_solid(context, solid, input_arg_dicts):
    check.inst_param(context, 'context', SolidExecutionContext)
    check.inst_param(solid, 'solid', Solid)
    check.dict_param(input_arg_dicts, 'input_arg_dicts', key_type=str, value_type=dict)

    materialized_inputs = materialize_all_inputs(context, solid, input_arg_dicts)
    return pipeline_solid_in_memory(context, solid, materialized_inputs)


def pipeline_solid_in_memory(context, solid, materialized_inputs):
    '''
    Given inputs that are already materialized in memory. Evaluation all inputs expectations,
    execute the core transform, and then evaluate all output expectations.
    '''
    check.inst_param(context, 'context', SolidExecutionContext)
    check.inst_param(solid, 'solid', Solid)
    check.dict_param(materialized_inputs, 'materialized_inputs', key_type=str)

    all_run_result = execute_all_input_expectations(context, solid, materialized_inputs)

    if not all_run_result.success:
        return SolidExecutionResult(
            success=False,
            materialized_output=None,
            solid=solid,
            reason=SolidExecutionFailureReason.EXPECTATION_FAILURE,
            failed_expectation_results=all_run_result.all_fails,
        )

    context.info('Executing core transform')

    materialized_output = execute_core_transform(context, solid.transform_fn, materialized_inputs)

    if isinstance(materialized_output, SolidExecutionResult):
        check.invariant(
            not materialized_output.success,
            'only failed things should return an execution result right here'
        )
        return materialized_output

    output_expectation_failures = []
    for output_expectation_def in solid.output_expectations:
        output_expectation_result = execute_output_expectation(
            context, output_expectation_def, materialized_output
        )
        if not output_expectation_result.success:
            output_expectation_failures.append(output_expectation_result)

    if output_expectation_failures:
        return SolidExecutionResult(
            success=False,
            materialized_output=None,
            solid=solid,
            reason=SolidExecutionFailureReason.EXPECTATION_FAILURE,
            failed_expectation_results=output_expectation_failures,
        )

    return materialized_output


def execute_solid(context, solid, input_arg_dicts):
    check.inst_param(context, 'context', SolidExecutionContext)
    check.inst_param(solid, 'solid', Solid)
    check.dict_param(input_arg_dicts, 'input_arg_dicts', key_type=str, value_type=dict)

    results = list(execute_pipeline(context, SolidPipeline(solids=[solid]), input_arg_dicts))

    check.invariant(len(results) == 1, 'must be one result got ' + str(len(results)))

    execution_result = results[0]

    check.invariant(execution_result.name == solid.name)

    return execution_result


def output_solid(context, solid, input_arg_dicts, output_type, output_arg_dict):
    check.inst_param(context, 'context', SolidExecutionContext)
    check.inst_param(solid, 'solid', Solid)
    check.dict_param(input_arg_dicts, 'input_arg_dicts', key_type=str, value_type=dict)
    check.str_param(output_type, 'output_type')
    check.dict_param(output_arg_dict, 'output_arg_dict', key_type=str)

    results = list(
        output_pipeline(
            context,
            SolidPipeline(solids=[solid]),
            input_arg_dicts,
            output_configs=[
                OutputConfig(name=solid.name, output_type=output_type, output_args=output_arg_dict)
            ]
        )
    )

    check.invariant(len(results) == 1, 'must be one result got ' + str(len(results)))

    execution_result = results[0]

    check.invariant(execution_result.name == solid.name)

    return execution_result


def _select_keys(ddict1, ddict2, keys):
    ddict = {**ddict1, **ddict2}
    return {key: ddict[key] for key in keys}


def execute_solid_in_pipeline(context, pipeline, input_arg_dicts, output_name):
    check.inst_param(context, 'context', SolidExecutionContext)
    check.inst_param(pipeline, 'pipeline', SolidPipeline)
    check.dict_param(input_arg_dicts, 'input_arg_dicts', key_type=str, value_type=dict)
    check.str_param(output_name, 'output_name')

    for result in execute_pipeline(context, pipeline, input_arg_dicts, [output_name]):
        if result.name == output_name:
            return result

    check.failed('Result ' + output_name + ' not found!')


def _execute_pipeline_solid_step(context, solid, input_arg_dicts, materialized_values):
    # The value produce by an inputs is potentially different per solid.
    # This is allowed so that two solids that do different materialization of the
    # same exact input (e.g. the same file) don't have to create additional solids
    # to account for this.

    input_values = {}

    context.info('About to materialize and gather all inputs')

    for inp in solid.inputs:
        if inp.name not in materialized_values and inp.name not in input_values:
            materialized = materialize_input(context, inp, input_arg_dicts[inp.name])
            input_values[inp.name] = materialized

    selected_values = _select_keys(input_values, materialized_values, solid.input_names)

    # This call does all input and output expectations, as well as the core transform
    materialized_output = pipeline_solid_in_memory(context, solid, selected_values)

    if isinstance(materialized_output, SolidExecutionResult):
        check.invariant(not materialized_output.success, 'early return should only be failure')
        return materialized_output

    check.invariant(solid.name not in materialized_values, 'should be not in materialized values')

    materialized_values[solid.name] = materialized_output

    return SolidExecutionResult(
        success=True,
        solid=solid,
        materialized_output=materialized_values[solid.name],
        exception=None
    )


def execute_pipeline(context, pipeline, input_arg_dicts, through_solids=None):
    check.inst_param(context, 'context', SolidExecutionContext)
    check.inst_param(pipeline, 'pipeline', SolidPipeline)
    check.dict_param(input_arg_dicts, 'input_arg_dicts', key_type=str, value_type=dict)
    check.opt_list_param(through_solids, 'through_solids', of_type=str)

    input_names = list(input_arg_dicts.keys())
    output_names = pipeline.solid_names if not through_solids else through_solids

    for output_name in output_names:
        unprovided_inputs = pipeline.solid_graph.compute_unprovided_inputs(
            input_names=input_names, output_name=output_name
        )
        if unprovided_inputs:
            check.failed(
                'Failed to provide inputs {unprovided_inputs} for solid {name}'.format(
                    unprovided_inputs=unprovided_inputs, name=output_name
                )
            )

    # Given the inputs and outputs specific, create the subgraph of the pipeline
    # necessary to complete the computation
    execution_graph = pipeline.solid_graph.create_execution_graph(output_names, input_names)

    materialized_values = {}

    for solid in execution_graph.topological_solids:

        try:
            with context.value('solid', solid.name):
                materialized_output = _execute_pipeline_solid_step(
                    context, solid, input_arg_dicts, materialized_values
                )

            yield materialized_output

            if not materialized_output.success:
                break

        except SolidExecutionError as see:
            yield SolidExecutionResult(
                success=False,
                reason=SolidExecutionFailureReason.USER_CODE_ERROR,
                solid=solid,
                materialized_output=None,
                exception=see,
            )


OutputConfig = namedtuple('OutputConfig', 'name output_type, output_args')


def execute_pipeline_and_collect(context, pipeline, input_arg_dicts, through_solids=None):
    results = []
    for result in execute_pipeline(context, pipeline, input_arg_dicts, through_solids):
        results.append(copy.deepcopy(result))
    return results


def output_pipeline_and_collect(context, pipeline, input_arg_dicts, output_configs):
    check.inst_param(context, 'context', SolidExecutionContext)
    check.inst_param(pipeline, 'pipeline', SolidPipeline)
    check.dict_param(input_arg_dicts, 'input_arg_dicts', key_type=str, value_type=dict)
    check.list_param(output_configs, 'output_configs', of_type=OutputConfig)

    results = []
    for result in output_pipeline(context, pipeline, input_arg_dicts, output_configs):
        results.append(copy.deepcopy(result))
    return results


def output_pipeline(context, pipeline, input_arg_dicts, output_configs):
    check.inst_param(context, 'context', SolidExecutionContext)
    check.inst_param(pipeline, 'pipeline', SolidPipeline)
    check.dict_param(input_arg_dicts, 'input_arg_dicts', key_type=str, value_type=dict)
    check.list_param(output_configs, 'output_configs', of_type=OutputConfig)

    output_dict = {output_config.name: output_config for output_config in output_configs}

    for result in execute_pipeline(
        context, pipeline, input_arg_dicts, through_solids=list(output_dict.keys())
    ):
        if not result.success:
            yield result
            break

        if result.name in output_dict:
            output_type = output_dict[result.name].output_type
            output_arg_dict = output_dict[result.name].output_args
            output_type_def = result.solid.output_type_def_named(output_type)
            with context.value('solid', result.name), \
                context.value('output_type', output_type_def.name), \
                context.value('output_args', output_arg_dict):
                try:
                    execute_output(
                        context, output_type_def, output_arg_dict, result.materialized_output
                    )
                except SolidExecutionError as see:
                    yield SolidExecutionResult(
                        success=False,
                        solid=result.solid,
                        reason=SolidExecutionFailureReason.USER_CODE_ERROR,
                        exception=see,
                        materialized_output=result.materialized_output,
                    )
                    break

        yield result
