from contextlib import contextmanager
from enum import Enum

import check

from solidic.definitions import (
    Solid,
    SolidInputDefinition,
    SolidOutputTypeDefinition,
    SolidExpectationDefinition,
    SolidExpectationResult,
)


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
    pass


class SolidExecutionResult:
    def __init__(self, success, reason=None, exception=None, failed_expectation_result=None):
        self.success = check.bool_param(success, 'success')
        if not success:
            check.param_invariant(
                isinstance(reason, SolidExecutionFailureReason), 'reason',
                'Must provide a reason is result is a failure'
            )
        self.reason = reason
        self.exception = check.opt_inst_param(exception, 'exception', Exception)
        ## CONSIDER REMOVING THIS AND OPT FOR COLLECTION OF RESULTS
        self.failed_expectation_result = failed_expectation_result


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

    expected_args = set(input_definition.argument_def_dict.keys())
    received_args = set(arg_dict.keys())
    if expected_args != received_args:
        raise SolidTypeError(
            'Argument mismatch in input {input_name}. Expected {expected} got {received}'.format(
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
        return input_definition.input_fn(arg_dict)


def evaluate_input_expectation(context, expectation_def, materialized_input):
    check.inst_param(context, 'context', SolidExecutionContext)
    check.inst_param(expectation_def, 'expectation_def', SolidExpectationDefinition)

    error_str = 'Error occured while evaluation expectation "{expectation_name}" in input'
    with user_code_error_boundary(error_str, expectation_name=expectation_def.name):
        expectation_result = expectation_def.expectation_fn(materialized_input)

    if not isinstance(expectation_result, SolidExpectationResult):
        raise SolidExecutionError('Must return SolidExpectationResult from expectation function')

    return expectation_result


def evaluate_output_expectation(context, expectation_def, materialized_output):
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
        return solid_transform_fn(**materialized_inputs)


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
        output_type_def.output_fn(materialized_output, output_arg_dict)


def execute_solid(context, solid, input_arg_dicts, output_type, output_arg_dict):
    check.inst_param(context, 'context', SolidExecutionContext)
    check.inst_param(solid, 'solid', Solid)
    check.dict_param(input_arg_dicts, 'input_arg_dicts', key_type=str, value_type=dict)
    check.str_param(output_type, 'output_type')
    check.dict_param(output_arg_dict, 'output_arg_dict', key_type=str)

    def inner_execute():
        materialized_inputs = {}

        for input_name, arg_dict in input_arg_dicts.items():
            input_def = solid.input_def_named(input_name)
            materialized_input = materialize_input(context, input_def, arg_dict)

            for input_expectation_def in input_def.expectations:
                input_expectation_result = evaluate_input_expectation(
                    context, input_expectation_def, materialized_input
                )
                if not input_expectation_result.success:
                    return SolidExecutionResult(
                        success=False,
                        reason=SolidExecutionFailureReason.EXPECTATION_FAILURE,
                        failed_expectation_result=input_expectation_result,
                    )

            materialized_inputs[input_name] = materialized_input

        materialized_output = execute_core_transform(
            context, solid.transform_fn, materialized_inputs
        )

        output_type_def = solid.output_type_def_named(output_type)

        for output_expectation_def in output_type_def.expectations:
            output_expectation_result = evaluate_output_expectation(
                context, output_expectation_def, materialized_output
            )
            if not output_expectation_result.success:
                return SolidExecutionResult(
                    success=False,
                    reason=SolidExecutionFailureReason.EXPECTATION_FAILURE,
                    failed_expectation_result=output_expectation_result,
                )

        execute_output(context, output_type_def, output_arg_dict, materialized_output)

        return SolidExecutionResult(success=True)

    try:
        return inner_execute()
    except SolidExecutionError as see:
        return SolidExecutionResult(
            success=False, reason=SolidExecutionFailureReason.USER_CODE_ERROR, exception=see
        )
    except Exception as e:  # pylint: disable=W0703
        return SolidExecutionResult(
            success=False, reason=SolidExecutionFailureReason.FRAMEWORK_ERROR, exception=e
        )
