import pytest

from dagster import (ArgumentDefinition, types)
from dagster.core.argument_handling import validate_args
from dagster.core.errors import DagsterTypeError


def _validate(argument_def_dict, arg_dict):
    return validate_args(argument_def_dict, arg_dict, 'dummy')


def _single_required_string_arg_def_dict():
    return {'string_arg': ArgumentDefinition(types.String)}


def _multiple_required_args_def_dict():
    return {
        'arg_one': ArgumentDefinition(types.String),
        'arg_two': ArgumentDefinition(types.String)
    }


def _single_optional_string_arg_def_dict():
    return {'optional_arg': ArgumentDefinition(types.String, is_optional=True)}


def _single_optional_string_arg_def_dict_with_default():
    return {
        'optional_arg':
        ArgumentDefinition(types.String, is_optional=True, default_value='some_default')
    }


def _mixed_required_optional_string_arg_def_dict_with_default():
    return {
        'optional_arg':
        ArgumentDefinition(types.String, is_optional=True, default_value='some_default'),
        'required_arg':
        ArgumentDefinition(types.String, is_optional=False),
        'optional_arg_no_default':
        ArgumentDefinition(types.String, is_optional=True),
    }


def test_empty():
    _validate({}, {})


def test_required_single_arg_passing():
    _validate(_single_required_string_arg_def_dict(), {'string_arg': 'value'})
    _validate(_single_required_string_arg_def_dict(), {'string_arg': None})


def test_multiple_required_arg_passing():
    _validate(_multiple_required_args_def_dict(), {'arg_one': 'value_one', 'arg_two': 'value_two'})
    _validate(_multiple_required_args_def_dict(), {'arg_one': 'value_one', 'arg_two': None})


def test_single_required_arg_failures():
    with pytest.raises(DagsterTypeError):
        _validate(_single_required_string_arg_def_dict(), {})

    with pytest.raises(DagsterTypeError):
        _validate(_single_required_string_arg_def_dict(), {'extra': 'yup'})

    with pytest.raises(DagsterTypeError):
        _validate(_single_required_string_arg_def_dict(), {'string_arg': 'yupup', 'extra': 'yup'})

    with pytest.raises(DagsterTypeError):
        _validate(_single_required_string_arg_def_dict(), {'string_arg': 1})


def test_multiple_required_args_failing():
    with pytest.raises(DagsterTypeError):
        _validate(_multiple_required_args_def_dict(), {})

    with pytest.raises(DagsterTypeError):
        _validate(_multiple_required_args_def_dict(), {'arg_one': 'yup'})

    with pytest.raises(DagsterTypeError):
        _validate(_multiple_required_args_def_dict(), {'arg_one': 'yup', 'extra': 'yup'})

    with pytest.raises(DagsterTypeError):
        _validate(_multiple_required_args_def_dict(), {'arg_one': 'value_one', 'arg_two': 2})


def test_single_optional_arg_passing():
    assert _validate(_single_optional_string_arg_def_dict(), {'optional_arg': 'value'}) == {
        'optional_arg': 'value'
    }
    assert _validate(_single_optional_string_arg_def_dict(), {}) == {}

    assert _validate(_single_optional_string_arg_def_dict(), {'optional_arg': None}) == {
        'optional_arg': None
    }


def test_single_optional_arg_failing():
    with pytest.raises(DagsterTypeError):
        _validate(_single_optional_string_arg_def_dict(), {'optional_arg': 1})

    with pytest.raises(DagsterTypeError):
        _validate(_single_optional_string_arg_def_dict(), {'optional_argdfd': 1})


def test_single_optional_arg_passing_with_default():
    assert _validate(_single_optional_string_arg_def_dict_with_default(), {}) == {
        'optional_arg': 'some_default'
    }

    assert _validate(
        _single_optional_string_arg_def_dict_with_default(), {'optional_arg': 'override'}
    ) == {
        'optional_arg': 'override'
    }


def test_mixed_args_passing():
    assert _validate(
        _mixed_required_optional_string_arg_def_dict_with_default(), {
            'optional_arg': 'value_one',
            'required_arg': 'value_two',
        }
    ) == {
        'optional_arg': 'value_one',
        'required_arg': 'value_two',
    }

    assert _validate(
        _mixed_required_optional_string_arg_def_dict_with_default(), {
            'required_arg': 'value_two',
        }
    ) == {
        'optional_arg': 'some_default',
        'required_arg': 'value_two',
    }

    assert _validate(
        _mixed_required_optional_string_arg_def_dict_with_default(), {
            'required_arg': 'value_two',
            'optional_arg_no_default': 'value_three',
        }
    ) == {
        'optional_arg': 'some_default',
        'required_arg': 'value_two',
        'optional_arg_no_default': 'value_three',
    }
