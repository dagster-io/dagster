from dagster import (
    ConfigDefinition,
    types,
    Field,
)


def test_noop_config():
    assert ConfigDefinition(types.Any)


def test_int_field():
    config_def = ConfigDefinition.config_dict({
        'int_field': Field(types.Int),
    })

    assert config_def.config_type.evaluate_value({'int_field': 1}).value == {'int_field': 1}


def test_int_fails():
    config_def = ConfigDefinition.config_dict({
        'int_field': Field(types.Int),
    })

    assert not config_def.config_type.evaluate_value({'int_field': 'fjkdj'}).success

    assert not config_def.config_type.evaluate_value({'int_field': True}).success


def test_default_arg():
    config_def = ConfigDefinition.config_dict(
        {
            'int_field': Field(types.Int, default_value=2, is_optional=True),
        }
    )

    assert config_def.config_type.evaluate_value({}).value == {'int_field': 2}


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
    assert _validate(_single_required_string_config_dict(), {'string_field': 'value'}).success
    assert _validate(_single_required_string_config_dict(), {'string_field': None}).success

    assert not _validate(_single_required_string_config_dict(), {}).success

    assert not _validate(_single_required_string_config_dict(), {'extra': 'yup'}).success

    assert not _validate(
        _single_required_string_config_dict(), {
            'string_field': 'yupup',
            'extra': 'yup'
        }
    ).success

    assert not _validate(_single_required_string_config_dict(), {'string_field': 1}).success


def test_multiple_required_fields_passing():
    assert _validate(
        _multiple_required_fields_config_dict(),
        {
            'field_one': 'value_one',
            'field_two': 'value_two',
        },
    ).success
    assert _validate(
        _multiple_required_fields_config_dict(),
        {
            'field_one': 'value_one',
            'field_two': None,
        },
    ).success


def test_multiple_required_fields_failing():
    assert not _validate(_multiple_required_fields_config_dict(), {}).success

    assert not _validate(_multiple_required_fields_config_dict(), {'field_one': 'yup'}).success

    assert not _validate(
        _multiple_required_fields_config_dict(), {
            'field_one': 'yup',
            'extra': 'yup'
        }
    ).success

    assert not _validate(
        _multiple_required_fields_config_dict(), {
            'field_one': 'value_one',
            'field_two': 2
        }
    ).success


def test_single_optional_field_passing():
    assert _validate(_single_optional_string_config_dict(), {
        'optional_field': 'value'
    }).value == {
        'optional_field': 'value'
    }
    assert _validate(_single_optional_string_config_dict(), {}).value == {}

    assert _validate(_single_optional_string_config_dict(), {
        'optional_field': None
    }).value == {
        'optional_field': None
    }


def test_single_optional_field_failing():
    assert not _validate(_single_optional_string_config_dict(), {'optional_field': 1}).success

    assert not _validate(_single_optional_string_config_dict(), {'dlkjfalksdjflksaj': 1}).success


def test_single_optional_field_passing_with_default():
    assert _validate(_single_optional_string_field_config_dict_with_default(), {}).value == {
        'optional_field': 'some_default'
    }

    assert _validate(
        _single_optional_string_field_config_dict_with_default(), {
            'optional_field': 'override'
        }
    ).value == {
        'optional_field': 'override'
    }


def test_mixed_args_passing():
    assert _validate(
        _mixed_required_optional_string_config_dict_with_default(), {
            'optional_arg': 'value_one',
            'required_arg': 'value_two',
        }
    ).value == {
        'optional_arg': 'value_one',
        'required_arg': 'value_two',
    }

    assert _validate(
        _mixed_required_optional_string_config_dict_with_default(), {
            'required_arg': 'value_two',
        }
    ).value == {
        'optional_arg': 'some_default',
        'required_arg': 'value_two',
    }

    assert _validate(
        _mixed_required_optional_string_config_dict_with_default(), {
            'required_arg': 'value_two',
            'optional_arg_no_default': 'value_three',
        }
    ).value == {
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
    assert _validate(_single_nested_config(), {
        'nested': {
            'int_field': 2
        }
    }).value == {
        'nested': {
            'int_field': 2
        }
    }


def test_single_nested_config_failures():
    assert not _validate(_single_nested_config(), {'nested': 'dkjfdk'}).success

    assert not _validate(_single_nested_config(), {'nested': {'int_field': 'dkjfdk'}}).success

    assert not _validate(
        _single_nested_config(), {
            'nested': {
                'int_field': {
                    'too_nested': 'dkjfdk'
                }
            }
        }
    ).success


def test_nested_optional_with_default():
    assert _validate(_nested_optional_config_with_default(), {
        'nested': {
            'int_field': 2
        }
    }).value == {
        'nested': {
            'int_field': 2
        }
    }

    assert _validate(_nested_optional_config_with_default(), {
        'nested': {}
    }).value == {
        'nested': {
            'int_field': 3
        }
    }


def test_nested_optional_with_no_default():
    assert _validate(_nested_optional_config_with_no_default(), {
        'nested': {
            'int_field': 2
        }
    }).value == {
        'nested': {
            'int_field': 2
        }
    }

    assert _validate(_nested_optional_config_with_no_default(), {
        'nested': {}
    }).value == {
        'nested': {}
    }
