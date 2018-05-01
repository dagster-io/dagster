from contextlib import contextmanager

import check

from solidic.definitions import (
    Solid,
    SolidExecutionContext,
    SolidInputDefinition,
    SolidOutputTypeDefinition,
    SolidExpectationDefinition,
    SolidExpectationResult,
)


class SolidError(Exception):
    pass


class SolidTypeError(SolidError):
    '''Indicates an error in the solid type system (e.g. mismatched arguments)'''
    pass


class SolidExecutionError(SolidError):
    '''Indicates an error in user space code'''
    pass


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

    error_str = 'Error occured while evaluation expectation "{expectation_name}"'
    with user_code_error_boundary(error_str, expectation_name=expectation_def.name):
        expectation_result = expectation_def.expectation_fn(materialized_input)

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


def materialize_solid(context, solid, input_arg_dicts):
    check.inst_param(context, 'context', SolidExecutionContext)
    check.inst_param(solid, 'solid', Solid)
    check.dict_param(input_arg_dicts, 'input_arg_dicts', key_type=str, value_type=dict)

    materialized_inputs = {}

    for input_name, arg_dict in input_arg_dicts.items():
        input_def = solid.input_def_named(input_name)
        materialized_input = materialize_input(context, input_def, arg_dict)
        materialized_inputs[input_name] = materialized_input

    materialized_output = execute_core_transform(context, solid.transform_fn, materialized_inputs)
    return materialized_output


def execute_solid(context, solid, input_arg_dicts, output_type, output_arg_dict):
    check.inst_param(context, 'context', SolidExecutionContext)
    check.inst_param(solid, 'solid', Solid)
    check.dict_param(input_arg_dicts, 'input_arg_dicts', key_type=str, value_type=dict)
    check.str_param(output_type, 'output_type')
    check.dict_param(output_arg_dict, 'output_arg_dict', key_type=str)

    materialized_output = materialize_solid(context, solid, input_arg_dicts)
    output_type_def = solid.output_type_def_named(output_type)
    execute_output(context, output_type_def, output_arg_dict, materialized_output)
