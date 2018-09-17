from collections import namedtuple

import pytest
from dagster import (
    ConfigDefinition,
    types,
    Field,
    DagsterEvaluateValueError,
)


def test_noop_config():
    assert ConfigDefinition(types.Any)


def test_int_field():
    config_def = ConfigDefinition.config_dict({
        'int_field': Field(types.Int),
    })

    assert config_def.config_type.evaluate_value({'int_field': 1}) == {'int_field': 1}


def test_int_fails():
    config_def = ConfigDefinition.config_dict({
        'int_field': Field(types.Int),
    })

    with pytest.raises(DagsterEvaluateValueError):
        config_def.config_type.evaluate_value({'int_field': 'fjkdj'})

    with pytest.raises(DagsterEvaluateValueError):
        config_def.config_type.evaluate_value({'int_field': True})


def test_default_arg():
    config_def = ConfigDefinition.config_dict(
        {
            'int_field': Field(types.Int, default_value=2, is_optional=True),
        }
    )

    assert config_def.config_type.evaluate_value({}) == {'int_field': 2}


def _single_required_string_config_dict():
    return ConfigDefinition.config_dict({'string_field': Field(types.String)})


def _multiple_required_fields_config_dict():
    return ConfigDefinition.config_dict(
        {
            'field_one': Field(types.String),
            'field_two': Field(types.String),
        }
    )


def _single_optional_string_config_dict():
    return ConfigDefinition.config_dict({'optional_field': Field(types.String, is_optional=True)})


def _single_optional_string_field_config_dict_with_default():
    optional_field_def = Field(
        types.String,
        is_optional=True,
        default_value='some_default',
    )
    return ConfigDefinition.config_dict({'optional_field': optional_field_def})


def _mixed_required_optional_string_config_dict_with_default():
    return ConfigDefinition.config_dict(
        {
            'optional_arg': Field(
                types.String,
                is_optional=True,
                default_value='some_default',
            ),
            'required_arg': Field(types.String, is_optional=False),
            'optional_arg_no_default': Field(types.String, is_optional=True),
        }
    )


def _validate(config_def, value):
    return config_def.config_type.evaluate_value(value)


def test_single_required_string_field_config_type():
    assert _validate(_single_required_string_config_dict(), {'string_field': 'value'}) == {
        'string_field': 'value'
    }
    assert _validate(_single_required_string_config_dict(), {'string_field': None}) == {
        'string_field': None
    }

    with pytest.raises(DagsterEvaluateValueError):
        _validate(_single_required_string_config_dict(), {})

    with pytest.raises(DagsterEvaluateValueError):
        _validate(_single_required_string_config_dict(), {'extra': 'yup'})

    with pytest.raises(DagsterEvaluateValueError):
        _validate(_single_required_string_config_dict(), {'string_field': 'yupup', 'extra': 'yup'})

    with pytest.raises(DagsterEvaluateValueError):
        _validate(_single_required_string_config_dict(), {'string_field': 1})


def test_multiple_required_fields_passing():
    assert _validate(
        _multiple_required_fields_config_dict(),
        {
            'field_one': 'value_one',
            'field_two': 'value_two',
        },
    ) == {
        'field_one': 'value_one',
        'field_two': 'value_two',
    }

    assert _validate(
        _multiple_required_fields_config_dict(),
        {
            'field_one': 'value_one',
            'field_two': None,
        },
    ) == {
        'field_one': 'value_one',
        'field_two': None,
    }


def test_multiple_required_fields_failing():
    with pytest.raises(DagsterEvaluateValueError):
        _validate(_multiple_required_fields_config_dict(), {})

    with pytest.raises(DagsterEvaluateValueError):
        _validate(_multiple_required_fields_config_dict(), {'field_one': 'yup'})

    with pytest.raises(DagsterEvaluateValueError):
        _validate(_multiple_required_fields_config_dict(), {'field_one': 'yup', 'extra': 'yup'})

    with pytest.raises(DagsterEvaluateValueError):
        _validate(
            _multiple_required_fields_config_dict(), {
                'field_one': 'value_one',
                'field_two': 2
            }
        )


def test_single_optional_field_passing():
    assert _validate(_single_optional_string_config_dict(), {'optional_field': 'value'}) == {
        'optional_field': 'value'
    }
    assert _validate(_single_optional_string_config_dict(), {}) == {}

    assert _validate(_single_optional_string_config_dict(), {'optional_field': None}) == {
        'optional_field': None
    }


def test_single_optional_field_failing():
    with pytest.raises(DagsterEvaluateValueError):

        _validate(_single_optional_string_config_dict(), {'optional_field': 1})

    with pytest.raises(DagsterEvaluateValueError):
        _validate(_single_optional_string_config_dict(), {'dlkjfalksdjflksaj': 1})


def test_single_optional_field_passing_with_default():
    assert _validate(_single_optional_string_field_config_dict_with_default(), {}) == {
        'optional_field': 'some_default'
    }

    assert _validate(
        _single_optional_string_field_config_dict_with_default(), {'optional_field': 'override'}
    ) == {
        'optional_field': 'override'
    }


def test_mixed_args_passing():
    assert _validate(
        _mixed_required_optional_string_config_dict_with_default(), {
            'optional_arg': 'value_one',
            'required_arg': 'value_two',
        }
    ) == {
        'optional_arg': 'value_one',
        'required_arg': 'value_two',
    }

    assert _validate(
        _mixed_required_optional_string_config_dict_with_default(), {
            'required_arg': 'value_two',
        }
    ) == {
        'optional_arg': 'some_default',
        'required_arg': 'value_two',
    }

    assert _validate(
        _mixed_required_optional_string_config_dict_with_default(), {
            'required_arg': 'value_two',
            'optional_arg_no_default': 'value_three',
        }
    ) == {
        'optional_arg': 'some_default',
        'required_arg': 'value_two',
        'optional_arg_no_default': 'value_three',
    }


def _single_nested_config():
    return ConfigDefinition(
        config_type=types.ConfigDictionary(
            {
                'nested':
                Field(dagster_type=types.ConfigDictionary({
                    'int_field': Field(types.Int)
                })),
            }
        )
    )


def _nested_optional_config_with_default():
    return ConfigDefinition(
        config_type=types.ConfigDictionary(
            {
                'nested':
                Field(
                    dagster_type=types.ConfigDictionary(
                        {
                            'int_field': Field(
                                types.Int,
                                is_optional=True,
                                default_value=3,
                            )
                        }
                    )
                ),
            }
        )
    )


def _nested_optional_config_with_no_default():
    return ConfigDefinition(
        config_type=types.ConfigDictionary(
            {
                'nested':
                Field(
                    dagster_type=types.
                    ConfigDictionary({
                        'int_field': Field(
                            types.Int,
                            is_optional=True,
                        )
                    })
                ),
            }
        )
    )


def test_single_nested_config():
    assert _validate(_single_nested_config(), {'nested': {
        'int_field': 2
    }}) == {
        'nested': {
            'int_field': 2
        }
    }


def test_single_nested_config_failures():
    with pytest.raises(DagsterEvaluateValueError):
        _validate(_single_nested_config(), {'nested': 'dkjfdk'})

    with pytest.raises(DagsterEvaluateValueError):
        _validate(_single_nested_config(), {'nested': {'int_field': 'dkjfdk'}})

    with pytest.raises(DagsterEvaluateValueError):
        _validate(_single_nested_config(), {'nested': {'int_field': {'too_nested': 'dkjfdk'}}})


def test_nested_optional_with_default():
    assert _validate(_nested_optional_config_with_default(), {'nested': {
        'int_field': 2
    }}) == {
        'nested': {
            'int_field': 2
        }
    }

    assert _validate(_nested_optional_config_with_default(), {'nested': {}}) == {
        'nested': {
            'int_field': 3
        }
    }


def test_nested_optional_with_no_default():
    assert _validate(_nested_optional_config_with_no_default(), {'nested': {
        'int_field': 2
    }}) == {
        'nested': {
            'int_field': 2
        }
    }

    assert _validate(_nested_optional_config_with_no_default(), {'nested': {}}) == {'nested': {}}


CustomStructConfig = namedtuple('CustomStructConfig', 'foo bar')


class CustomStructConfigType(types.DagsterCompositeType):
    def __init__(self):
        super(CustomStructConfigType, self).__init__(
            'CustomStructConfigType',
            {
                'foo': Field(types.String),
                'bar': Field(types.Int),
            },
            lambda val: CustomStructConfig(foo=val['foo'], bar=val['bar']),
        )


def test_custom_composite_type():
    config_type = CustomStructConfigType()

    assert config_type.evaluate_value({
        'foo': 'some_string',
        'bar': 2
    }) == CustomStructConfig(
        foo='some_string', bar=2
    )

    with pytest.raises(DagsterEvaluateValueError):
        assert config_type.evaluate_value({
            'foo': 'some_string',
        })

    with pytest.raises(DagsterEvaluateValueError):
        assert config_type.evaluate_value({
            'bar': 'some_string',
        })

    with pytest.raises(DagsterEvaluateValueError):
        assert config_type.evaluate_value({
            'foo': 'some_string',
            'bar': 'not_an_int',
        })
