from collections import namedtuple

import pytest

from dagster import (
    ConfigDefinition,
    DagsterEvaluateValueError,
    DagsterInvalidDefinitionError,
    Field,
    PipelineContextDefinition,
    PipelineDefinition,
    SolidDefinition,
    types,
)

from dagster.core.types import (
    process_incoming_composite_value,
    ScopedConfigInfo,
)

from dagster.core.definitions import build_config_dict_type


def test_noop_config():
    assert ConfigDefinition(types.Any)


def test_int_field():
    config_def = ConfigDefinition.config_dict(
        'SingleRequiredInt',
        {
            'int_field': Field(types.Int),
        },
    )

    assert config_def.config_type.evaluate_value({'int_field': 1}) == {'int_field': 1}


def test_int_fails():
    config_def = ConfigDefinition.config_dict(
        'SingleRequiredInt', {
            'int_field': Field(types.Int),
        }
    )

    with pytest.raises(DagsterEvaluateValueError):
        config_def.config_type.evaluate_value({'int_field': 'fjkdj'})

    with pytest.raises(DagsterEvaluateValueError):
        config_def.config_type.evaluate_value({'int_field': True})


def test_default_arg():
    config_def = ConfigDefinition.config_dict(
        'TestDefaultArg', {
            'int_field': Field(types.Int, default_value=2, is_optional=True),
        }
    )

    assert config_def.config_type.evaluate_value({}) == {'int_field': 2}


def _single_required_string_config_dict():
    return ConfigDefinition.config_dict(
        'SingleRequiredField', {'string_field': Field(types.String)}
    )


def _multiple_required_fields_config_dict():
    return ConfigDefinition.config_dict(
        'MultipleRequiredFields', {
            'field_one': Field(types.String),
            'field_two': Field(types.String),
        }
    )


def _single_optional_string_config_dict():
    return ConfigDefinition.config_dict(
        'SingleOptionalString', {'optional_field': Field(types.String, is_optional=True)}
    )


def _single_optional_string_field_config_dict_with_default():
    optional_field_def = Field(
        types.String,
        is_optional=True,
        default_value='some_default',
    )
    return ConfigDefinition.config_dict(
        'SingleOptionalStringWithDefault',
        {'optional_field': optional_field_def},
    )


def _mixed_required_optional_string_config_dict_with_default():
    return ConfigDefinition.config_dict(
        'MixedRequired', {
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
            'ParentType', {
                'nested':
                Field(
                    dagster_type=types.ConfigDictionary(
                        'NestedType',
                        {'int_field': Field(types.Int)},
                    )
                ),
            }
        )
    )


def _nested_optional_config_with_default():
    return ConfigDefinition(
        config_type=types.ConfigDictionary(
            'ParentType', {
                'nested':
                Field(
                    dagster_type=types.ConfigDictionary(
                        'NestedType',
                        {'int_field': Field(
                            types.Int,
                            is_optional=True,
                            default_value=3,
                        )}
                    )
                ),
            }
        )
    )


def _nested_optional_config_with_no_default():
    nested_type = types.ConfigDictionary(
        'NestedType',
        {
            'int_field': Field(
                types.Int,
                is_optional=True,
            ),
        },
    )
    return ConfigDefinition(
        config_type=types.ConfigDictionary(
            'ParentType',
            {'nested': Field(dagster_type=nested_type)},
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
        )

    def evaluate_value(self, value):
        if value is not None and not isinstance(value, dict):
            raise DagsterEvaluateValueError('Incoming value for composite must be dict')

        return process_incoming_composite_value(
            self,
            value,
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


def single_elem(ddict):
    return list(ddict.items())[0]


def test_build_config_dict_type():
    single_cd_type = build_config_dict_type(
        ['PipelineName', 'SingleField'],
        {'foo': types.Field(types.String)},
        ScopedConfigInfo(
            pipeline_def_name='pipeline_name',
            solid_def_name='single_field',
        ),
    )
    assert isinstance(single_cd_type, types.ConfigDictionary)
    assert single_cd_type.name == 'PipelineName.SingleField.ConfigDict'
    assert len(single_cd_type.field_dict) == 1
    foo_name, foo_field = single_elem(single_cd_type.field_dict)
    assert foo_name == 'foo'
    assert foo_field.dagster_type is types.String


def test_build_single_nested():
    def _assert_facts(single_nested):
        assert single_nested.name == 'PipelineName.Solid.SolidName.ConfigDict'
        assert set(single_nested.field_dict.keys()) == set(['foo', 'nested_dict'])

        assert single_nested.field_dict['nested_dict'].is_optional is False
        nested_field_type = single_nested.field_dict['nested_dict'].dagster_type

        assert isinstance(nested_field_type, types.ConfigDictionary)
        assert nested_field_type.name == 'PipelineName.Solid.SolidName.NestedDict.ConfigDict'
        assert nested_field_type.field_name_set == set(['bar'])

    old_style_config_def = ConfigDefinition(
        types.ConfigDictionary(
            'PipelineName.Solid.SolidName.ConfigDict',
            {
                'foo':
                types.Field(types.String),
                'nested_dict':
                types.Field(
                    types.ConfigDictionary(
                        'PipelineName.Solid.SolidName.NestedDict.ConfigDict',
                        {
                            'bar': types.Field(types.String),
                        },
                    ),
                ),
            },
        ),
    )

    _assert_facts(old_style_config_def.config_type)

    single_nested_manual = build_config_dict_type(
        ['PipelineName', 'Solid', 'SolidName'],
        {
            'foo': types.Field(types.String),
            'nested_dict': {
                'bar': types.Field(types.String),
            },
        },
        ScopedConfigInfo(
            pipeline_def_name='pipeline_name',
            solid_def_name='solid_name',
        ),
    )

    _assert_facts(single_nested_manual)

    nested_from_config_def = ConfigDefinition.solid_config_dict(
        'pipeline_name',
        'solid_name',
        {
            'foo': types.Field(types.String),
            'nested_dict': {
                'bar': types.Field(types.String),
            },
        },
    )

    _assert_facts(nested_from_config_def.config_type)


def test_build_double_nested():
    double_config_type = ConfigDefinition.context_config_dict(
        'some_pipeline',
        'some_context',
        {
            'level_one': {
                'level_two': {
                    'field': types.Field(types.String)
                }
            }
        },
    ).config_type

    assert double_config_type.name == 'SomePipeline.Context.SomeContext.ConfigDict'

    level_one_type = double_config_type.field_dict['level_one'].dagster_type

    assert isinstance(level_one_type, types.ConfigDictionary)
    assert level_one_type.name == 'SomePipeline.Context.SomeContext.LevelOne.ConfigDict'
    assert level_one_type.field_name_set == set(['level_two'])

    level_two_type = level_one_type.field_dict['level_two'].dagster_type

    assert level_two_type.name == 'SomePipeline.Context.SomeContext.LevelOne.LevelTwo.ConfigDict'
    assert level_two_type.field_name_set == set(['field'])


def test_build_optionality():
    optional_test_type = ConfigDefinition.solid_config_dict(
        'some_pipeline',
        'some_solid',
        {
            'required': {
                'value': types.Field(types.String),
            },
            'optional': {
                'value': types.Field(types.String, is_optional=True),
            }
        },
    ).config_type

    assert optional_test_type.field_dict['required'].is_optional is False
    assert optional_test_type.field_dict['optional'].is_optional is True


def test_pipeline_name_mismatch_error():
    with pytest.raises(DagsterInvalidDefinitionError, match='wrong pipeline name'):
        PipelineDefinition(
            name='pipeline_mismatch_test',
            solids=[
                SolidDefinition(
                    name='some_solid',
                    inputs=[],
                    outputs=[],
                    config_def=ConfigDefinition.solid_config_dict(
                        'wrong_pipeline',
                        'some_solid',
                        {},
                    ),
                    transform_fn=lambda *_args: None,
                ),
            ],
        )

    with pytest.raises(DagsterInvalidDefinitionError, match='wrong pipeline name'):
        PipelineDefinition(
            name='pipeline_mismatch_test',
            solids=[],
            context_definitions={
                'some_context':
                PipelineContextDefinition(
                    context_fn=lambda *_args: None,
                    config_def=ConfigDefinition.context_config_dict(
                        'not_a_match',
                        'some_context',
                        {},
                    )
                )
            }
        )


def test_solid_name_mismatch():
    with pytest.raises(DagsterInvalidDefinitionError, match='wrong solid name'):
        PipelineDefinition(
            name='solid_name_mismatch',
            solids=[
                SolidDefinition(
                    name='dont_match_me',
                    inputs=[],
                    outputs=[],
                    config_def=ConfigDefinition.solid_config_dict(
                        'solid_name_mismatch',
                        'nope',
                        {},
                    ),
                    transform_fn=lambda *_args: None,
                ),
            ],
        )

    with pytest.raises(DagsterInvalidDefinitionError, match='context_config_dict'):
        PipelineDefinition(
            name='solid_name_mismatch',
            solids=[
                SolidDefinition(
                    name='dont_match_me',
                    inputs=[],
                    outputs=[],
                    config_def=ConfigDefinition.context_config_dict(
                        'solid_name_mismatch',
                        'dont_match_me',
                        {},
                    ),
                    transform_fn=lambda *_args: None,
                ),
            ],
        )


def test_context_name_mismatch():
    with pytest.raises(DagsterInvalidDefinitionError, match='wrong context name'):
        PipelineDefinition(
            name='context_name_mismatch',
            solids=[],
            context_definitions={
                'test':
                PipelineContextDefinition(
                    context_fn=lambda *_args: None,
                    config_def=ConfigDefinition.context_config_dict(
                        'context_name_mismatch',
                        'nope',
                        {},
                    )
                )
            }
        )

    with pytest.raises(DagsterInvalidDefinitionError, match='solid_config_dict'):
        PipelineDefinition(
            name='context_name_mismatch',
            solids=[],
            context_definitions={
                'test':
                PipelineContextDefinition(
                    context_fn=lambda *_args: None,
                    config_def=ConfigDefinition.solid_config_dict(
                        'context_name_mismatch',
                        'some_solid',
                        {},
                    )
                )
            }
        )
