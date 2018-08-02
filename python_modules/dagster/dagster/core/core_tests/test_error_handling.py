import pytest

from dagster import check

from dagster.utils.compatability import create_custom_source_input

from dagster.core.execution import (
    _read_source,
    _execute_core_transform,
    _execute_materialization,
    ExecutionContext,
    MaterializationDefinition,
)

from dagster.core.errors import DagsterUserCodeExecutionError


def create_test_context():
    return ExecutionContext()


def test_basic_source_runtime_error_handling():
    def source_fn_inst(_context, _arg_dict):
        raise Exception('a user error')

    erroring_input = create_custom_source_input(
        name='some_input', source_fn=source_fn_inst, argument_def_dict={}
    )

    with pytest.raises(DagsterUserCodeExecutionError):
        _read_source(create_test_context(), erroring_input.sources[0], {})


def test_basic_core_transform_error_handling():
    def transform_fn(an_input):
        check.str_param(an_input, 'an_input')
        raise Exception('exception during core transform')

    with pytest.raises(DagsterUserCodeExecutionError):
        _execute_core_transform(
            create_test_context(),
            transform_fn,
            {'an_input': 'value'},
        )


def test_basic_materialization_runtime_error_handling():
    def materialization_fn_inst(_data, arg_dict):
        assert arg_dict == {}
        raise Exception('error during output')

    materialization_def = MaterializationDefinition(
        name='CUSTOM', materialization_fn=materialization_fn_inst, argument_def_dict={}
    )

    with pytest.raises(DagsterUserCodeExecutionError):
        _execute_materialization(
            create_test_context(), materialization_def, arg_dict={}, value='whatever'
        )
