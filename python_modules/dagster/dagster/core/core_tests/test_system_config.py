import pytest

from dagster import (
    DagsterEvaluateConfigValueError,
    ExecutionContext,
    Field,
    PipelineContextDefinition,
    PipelineDefinition,
    SolidDefinition,
    config,
    types,
    execute_pipeline,
)

from dagster.core.config_types import (
    ContextConfigType,
    EnvironmentConfigType,
    ExecutionConfigType,
    ExpectationsConfigType,
    SolidConfigType,
    SolidDictionaryType,
    SpecificContextConfig,
)

from dagster.core.evaluator import evaluate_config_value

from dagster.core.test_utils import throwing_evaluate_config_value


def test_context_config_any():
    context_defs = {
        'test':
        PipelineContextDefinition(
            config_field=Field(types.Any),
            context_fn=lambda *args: ExecutionContext(),
        )
    }

    context_config_type = ContextConfigType('something', context_defs)

    assert context_config_type.type_attributes.is_system_config

    output = throwing_evaluate_config_value(context_config_type, {'test': {'config': 1}})
    assert output.name == 'test'
    assert output.config == 1


def test_context_config():
    context_defs = {
        'test':
        PipelineContextDefinition(
            config_field=Field(dagster_type=types.Dict({
                'some_str': Field(types.String),
            })),
            context_fn=lambda *args: ExecutionContext(),
        )
    }

    context_config_type = ContextConfigType('something', context_defs)

    output = throwing_evaluate_config_value(
        context_config_type, {'test': {
            'config': {
                'some_str': 'something'
            }
        }}
    )
    assert isinstance(output, config.Context)
    assert output.name == 'test'
    assert output.config == {'some_str': 'something'}


def test_default_expectations():
    expect_config_type = ExpectationsConfigType('some_name')
    assert throwing_evaluate_config_value(expect_config_type, {}).evaluate is True
    assert throwing_evaluate_config_value(expect_config_type, None).evaluate is True


def test_default_execution():
    execution_config_type = ExecutionConfigType('some_name')
    assert throwing_evaluate_config_value(execution_config_type,
                                          {}).serialize_intermediates is False
    assert throwing_evaluate_config_value(
        execution_config_type, None
    ).serialize_intermediates is False
    assert execution_config_type.type_attributes.is_system_config


def test_default_context_config():
    pipeline_def = PipelineDefinition(
        solids=[
            SolidDefinition(
                name='some_solid',
                inputs=[],
                outputs=[],
                transform_fn=lambda *args: None,
            ),
        ],
    )

    context_config_type = ContextConfigType(pipeline_def.name, pipeline_def.context_definitions)
    assert 'default' in context_config_type.field_dict
    assert context_config_type.field_dict['default'].is_optional
    default_context_config_type = context_config_type.field_dict['default'].dagster_type

    assert isinstance(default_context_config_type, SpecificContextConfig)
    assert 'config' in default_context_config_type.field_dict

    context_dict = throwing_evaluate_config_value(context_config_type, {})

    assert 'default' in context_dict


def test_provided_default_config():
    pipeline_def = PipelineDefinition(
        context_definitions={
            'some_context':
            PipelineContextDefinition(
                config_field=types.Field(
                    types.Dict(
                        {
                            'with_default_int':
                            Field(
                                types.Int,
                                is_optional=True,
                                default_value=23434,
                            ),
                        },
                    )
                ),
                context_fn=lambda *args: None
            )
        },
        solids=[
            SolidDefinition(
                name='some_solid',
                inputs=[],
                outputs=[],
                transform_fn=lambda *args: None,
            ),
        ],
    )

    env_type = EnvironmentConfigType(pipeline_def)
    some_context_field = env_type.field_dict['context'].dagster_type.field_dict['some_context']
    assert some_context_field.is_optional

    some_context_config_field = some_context_field.dagster_type.field_dict['config']
    assert some_context_config_field.is_optional
    assert some_context_config_field.default_value == {'with_default_int': 23434}

    assert some_context_field.default_value == {
        'config': {
            'with_default_int': 23434,
        },
        'resources': {},
    }

    result = evaluate_config_value(env_type, {})
    assert result.success
    assert result.value.context.name == 'some_context'
    assert env_type.type_attributes.is_system_config


def test_default_environment():
    pipeline_def = PipelineDefinition(
        solids=[
            SolidDefinition(
                name='some_solid',
                inputs=[],
                outputs=[],
                transform_fn=lambda *args: None,
            ),
        ],
    )

    env_type = EnvironmentConfigType(pipeline_def)
    env_obj = throwing_evaluate_config_value(env_type, {})

    assert env_obj.expectations.evaluate is True
    assert env_obj.execution.serialize_intermediates is False


def test_errors():
    context_defs = {
        'test':
        PipelineContextDefinition(
            config_field=Field(types.Dict({
                'required_int': types.Field(types.Int),
            }, )),
            context_fn=lambda *args: ExecutionContext(),
        )
    }

    context_config_type = ContextConfigType('something', context_defs)

    assert not evaluate_config_value(context_config_type, 1).success
    assert not evaluate_config_value(context_config_type, {}).success

    invalid_value = {'context_one': 1, 'context_two': 2}

    result = evaluate_config_value(context_config_type, invalid_value)
    assert not result.success
    assert len(result.errors) == 1


def test_select_context():
    context_defs = {
        'int_context':
        PipelineContextDefinition(
            config_field=Field(types.Int),
            context_fn=lambda *args: ExecutionContext(),
        ),
        'string_context':
        PipelineContextDefinition(
            config_field=Field(types.String),
            context_fn=lambda *args: ExecutionContext(),
        ),
    }

    context_config_type = ContextConfigType('something', context_defs)

    assert throwing_evaluate_config_value(context_config_type, {
        'int_context': {
            'config': 1
        },
    }) == config.Context(
        name='int_context',
        config=1,
    )

    assert throwing_evaluate_config_value(
        context_config_type, {
            'string_context': {
                'config': 'bar'
            },
        }
    ) == config.Context(
        name='string_context',
        config='bar',
    )

    # mismatched field type mismatch
    with pytest.raises(DagsterEvaluateConfigValueError):
        assert throwing_evaluate_config_value(
            context_config_type, {
                'int_context': {
                    'config': 'bar'
                },
            }
        )

    # mismatched field type mismatch
    with pytest.raises(DagsterEvaluateConfigValueError):
        assert throwing_evaluate_config_value(
            context_config_type, {
                'string_context': {
                    'config': 1
                },
            }
        )


def test_solid_config():
    solid_config_type = SolidConfigType('kdjfkd', Field(types.Int))
    solid_inst = throwing_evaluate_config_value(solid_config_type, {'config': 1})
    assert isinstance(solid_inst, config.Solid)
    assert solid_inst.config == 1
    assert solid_config_type.type_attributes.is_system_config


def test_expectations_config():
    expectations_config_type = ExpectationsConfigType('ksjdfkd')
    expectations = throwing_evaluate_config_value(expectations_config_type, {'evaluate': True})

    assert isinstance(expectations, config.Expectations)
    assert expectations.evaluate is True

    assert throwing_evaluate_config_value(expectations_config_type,
                                          {'evaluate': False
                                           }) == config.Expectations(evaluate=False)


def test_solid_dictionary_type():
    pipeline_def = define_test_solids_config_pipeline()

    solid_dict_type = SolidDictionaryType('foobar', pipeline_def)

    value = throwing_evaluate_config_value(
        solid_dict_type, {
            'int_config_solid': {
                'config': 1,
            },
            'string_config_solid': {
                'config': 'bar',
            },
        }
    )

    assert set(['int_config_solid', 'string_config_solid']) == set(value.keys())
    assert value == {
        'int_config_solid': config.Solid(1),
        'string_config_solid': config.Solid('bar'),
    }

    assert solid_dict_type.type_attributes.is_system_config

    for specific_solid_config_field in solid_dict_type.field_dict.values():
        specific_solid_config_type = specific_solid_config_field.dagster_type
        assert specific_solid_config_type.type_attributes.is_system_config
        user_config_field = specific_solid_config_field.dagster_type.field_dict['config']
        assert user_config_field.dagster_type.type_attributes.is_system_config is False


def define_test_solids_config_pipeline():
    return PipelineDefinition(
        solids=[
            SolidDefinition(
                name='int_config_solid',
                config_field=Field(types.Int, is_optional=True),
                inputs=[],
                outputs=[],
                transform_fn=lambda *args: None,
            ),
            SolidDefinition(
                name='string_config_solid',
                config_field=Field(types.String, is_optional=True),
                inputs=[],
                outputs=[],
                transform_fn=lambda *args: None,
            )
        ]
    )


def assert_has_fields(dtype, *fields):
    return set(dtype.field_dict.keys()) == set(fields)


def test_solid_configs_defaults():
    env_type = define_test_solids_config_pipeline().environment_type

    solids_field = env_type.field_named('solids')

    assert_has_fields(solids_field.dagster_type, 'int_config_solid', 'string_config_solid')

    int_solid_field = solids_field.dagster_type.field_named('int_config_solid')

    assert int_solid_field.is_optional
    # TODO: this is the test case the exposes the default dodginess
    assert int_solid_field.default_provided

    assert_has_fields(int_solid_field.dagster_type, 'config')

    int_solid_config_field = int_solid_field.dagster_type.field_named('config')

    assert int_solid_config_field.is_optional
    assert not int_solid_config_field.default_provided


def test_solid_dictionary_some_no_config():
    pipeline_def = PipelineDefinition(
        solids=[
            SolidDefinition(
                name='int_config_solid',
                config_field=Field(types.Int),
                inputs=[],
                outputs=[],
                transform_fn=lambda *args: None,
            ),
            SolidDefinition(
                name='no_config_solid',
                inputs=[],
                outputs=[],
                transform_fn=lambda *args: None,
            )
        ]
    )

    solid_dict_type = SolidDictionaryType('foobar', pipeline_def)

    value = throwing_evaluate_config_value(
        solid_dict_type, {
            'int_config_solid': {
                'config': 1,
            },
        }
    )

    assert set(['int_config_solid']) == set(value.keys())
    assert value == {
        'int_config_solid': config.Solid(1),
    }


def test_whole_environment():
    pipeline_def = PipelineDefinition(
        name='some_pipeline',
        context_definitions={
            'test':
            PipelineContextDefinition(
                config_field=Field(types.Any),
                context_fn=lambda *args: ExecutionContext(),
            )
        },
        solids=[
            SolidDefinition(
                name='int_config_solid',
                config_field=Field(types.Int),
                inputs=[],
                outputs=[],
                transform_fn=lambda *args: None,
            ),
            SolidDefinition(
                name='no_config_solid',
                inputs=[],
                outputs=[],
                transform_fn=lambda *args: None,
            )
        ]
    )

    environment_type = EnvironmentConfigType(pipeline_def)

    assert environment_type.field_dict['context'].dagster_type.name == 'SomePipeline.ContextConfig'
    solids_type = environment_type.field_dict['solids'].dagster_type
    assert solids_type.name == 'SomePipeline.SolidsConfigDictionary'
    assert solids_type.field_dict['int_config_solid'
                                  ].dagster_type.name == 'SomePipeline.SolidConfig.IntConfigSolid'
    assert environment_type.field_dict['expectations'
                                       ].dagster_type.name == 'SomePipeline.ExpectationsConfig'

    env = throwing_evaluate_config_value(
        environment_type, {
            'context': {
                'test': {
                    'config': 1,
                }
            },
            'solids': {
                'int_config_solid': {
                    'config': 123,
                },
            },
        }
    )

    assert isinstance(env, config.Environment)
    assert env.context == config.Context('test', 1)
    assert env.solids == {
        'int_config_solid': config.Solid(123),
    }
    assert env.expectations == config.Expectations(evaluate=True)


def test_solid_config_error():
    solid_dict_type = SolidDictionaryType('slkdfjkjdsf', define_test_solids_config_pipeline())
    int_solid_config = solid_dict_type.field_dict['int_config_solid'].dagster_type

    with pytest.raises(DagsterEvaluateConfigValueError, match='Field "notconfig" is not defined'):
        throwing_evaluate_config_value(int_solid_config, {'notconfig': 1})

    with pytest.raises(DagsterEvaluateConfigValueError):
        throwing_evaluate_config_value(int_solid_config, 1)


def test_execution_config():
    env_type = EnvironmentConfigType(define_test_solids_config_pipeline())
    env_obj = throwing_evaluate_config_value(
        env_type,
        {'execution': {
            'serialize_intermediates': True
        }},
    )
    assert isinstance(env_obj.execution, config.Execution)
    assert env_obj.execution.serialize_intermediates


def test_optional_solid_with_no_config():
    def _assert_config_none(info, value):
        assert info.config is value

    pipeline_def = PipelineDefinition(
        name='some_pipeline',
        solids=[
            SolidDefinition(
                name='int_config_solid',
                config_field=Field(types.Int),
                inputs=[],
                outputs=[],
                transform_fn=lambda info, _inputs: _assert_config_none(info, 234),
            ),
            SolidDefinition(
                name='no_config_solid',
                inputs=[],
                outputs=[],
                transform_fn=lambda info, _inputs: _assert_config_none(info, None),
            )
        ]
    )

    assert execute_pipeline(
        pipeline_def,
        {
            'solids': {
                'int_config_solid': {
                    'config': 234,
                },
            },
        },
    ).success


def test_optional_solid_with_optional_scalar_config():
    def _assert_config_none(info, value):
        assert info.config is value

    pipeline_def = PipelineDefinition(
        name='some_pipeline',
        solids=[
            SolidDefinition(
                name='int_config_solid',
                config_field=Field(types.Int, is_optional=True),
                inputs=[],
                outputs=[],
                transform_fn=lambda info, _inputs: _assert_config_none(info, 234),
            ),
        ]
    )

    env_type = pipeline_def.environment_type

    assert env_type.field_dict['solids'].is_optional is True

    solids_type = env_type.field_dict['solids'].dagster_type

    assert solids_type.field_dict['int_config_solid'].is_optional is True

    solids_default_obj = throwing_evaluate_config_value(solids_type, {})

    assert solids_default_obj['int_config_solid'].config is None

    env_obj = throwing_evaluate_config_value(env_type, {})

    assert env_obj.solids['int_config_solid'].config is None


def test_optional_solid_with_required_scalar_config():
    def _assert_config_none(info, value):
        assert info.config is value

    pipeline_def = PipelineDefinition(
        name='some_pipeline',
        solids=[
            SolidDefinition(
                name='int_config_solid',
                config_field=Field(types.Int),
                inputs=[],
                outputs=[],
                transform_fn=lambda info, _inputs: _assert_config_none(info, 234),
            ),
        ]
    )

    env_type = pipeline_def.environment_type

    assert env_type.field_dict['solids'].is_optional is False

    solids_type = env_type.field_dict['solids'].dagster_type

    assert solids_type.field_dict['int_config_solid'].is_optional is False

    int_config_solid_type = solids_type.field_dict['int_config_solid'].dagster_type

    assert_has_fields(int_config_solid_type, 'config')

    int_config_solid_config_field = int_config_solid_type.field_named('config')

    assert int_config_solid_config_field.is_optional is False

    execute_pipeline(
        pipeline_def,
        {'solids': {
            'int_config_solid': {
                'config': 234
            }
        }},
    )


def test_required_solid_with_required_subfield():
    pipeline_def = PipelineDefinition(
        name='some_pipeline',
        solids=[
            SolidDefinition(
                name='int_config_solid',
                config_field=Field(types.Dict({
                    'required_field': types.Field(types.String),
                }, )),
                inputs=[],
                outputs=[],
                transform_fn=lambda *_args: None,
            ),
        ]
    )

    env_type = EnvironmentConfigType(pipeline_def)

    assert env_type.field_dict['solids'].is_optional is False
    assert env_type.field_dict['solids'].dagster_type

    solids_type = env_type.field_dict['solids'].dagster_type
    assert solids_type.field_dict['int_config_solid'].is_optional is False
    int_config_solid_type = solids_type.field_dict['int_config_solid'].dagster_type
    assert int_config_solid_type.field_dict['config'].is_optional is False

    assert env_type.field_dict['context'].is_optional
    assert env_type.field_dict['execution'].is_optional
    assert env_type.field_dict['expectations'].is_optional

    env_obj = throwing_evaluate_config_value(
        env_type,
        {
            'solids': {
                'int_config_solid': {
                    'config': {
                        'required_field': 'foobar',
                    },
                },
            },
        },
    )

    assert env_obj.solids['int_config_solid'].config['required_field'] == 'foobar'

    with pytest.raises(DagsterEvaluateConfigValueError):
        throwing_evaluate_config_value(env_type, {'solids': {}})

    with pytest.raises(DagsterEvaluateConfigValueError):
        throwing_evaluate_config_value(env_type, {})


def test_optional_solid_with_optional_subfield():
    pipeline_def = PipelineDefinition(
        name='some_pipeline',
        solids=[
            SolidDefinition(
                name='int_config_solid',
                config_field=Field(
                    types.Dict({
                        'optional_field': types.Field(types.String, is_optional=True),
                    }),
                    is_optional=True,
                ),
                inputs=[],
                outputs=[],
                transform_fn=lambda *_args: None,
            ),
        ]
    )

    env_type = EnvironmentConfigType(pipeline_def)
    assert env_type.field_dict['solids'].is_optional
    assert env_type.field_dict['context'].is_optional
    assert env_type.field_dict['execution'].is_optional
    assert env_type.field_dict['expectations'].is_optional


def test_required_context_with_required_subfield():
    pipeline_def = PipelineDefinition(
        name='some_pipeline',
        solids=[],
        context_definitions={
            'some_context':
            PipelineContextDefinition(
                context_fn=lambda *args: None,
                config_field=Field(types.Dict({
                    'required_field': types.Field(types.String),
                }, ), ),
            ),
        },
    )

    env_type = EnvironmentConfigType(pipeline_def)
    assert env_type.field_dict['solids'].is_optional
    assert env_type.field_dict['context'].is_optional is False
    assert env_type.field_dict['execution'].is_optional
    assert env_type.field_dict['expectations'].is_optional

    context_union_config_type = env_type.field_dict['context'].dagster_type
    assert context_union_config_type.field_dict['some_context'].is_optional is False


def test_all_optional_field_on_single_context_dict():
    pipeline_def = PipelineDefinition(
        name='some_pipeline',
        solids=[],
        context_definitions={
            'some_context':
            PipelineContextDefinition(
                context_fn=lambda *args: None,
                config_field=types.Field(
                    types.Dict({
                        'optional_field': types.Field(types.String, is_optional=True),
                    }, )
                ),
            ),
        },
    )

    env_type = EnvironmentConfigType(pipeline_def)
    assert env_type.field_dict['solids'].is_optional
    assert env_type.field_dict['context'].is_optional
    assert env_type.field_dict['execution'].is_optional
    assert env_type.field_dict['expectations'].is_optional


def test_optional_and_required_context():
    pipeline_def = PipelineDefinition(
        name='some_pipeline',
        solids=[],
        context_definitions={
            'optional_field_context':
            PipelineContextDefinition(
                context_fn=lambda *args: None,
                config_field=Field(
                    dagster_type=types.Dict(
                        fields={
                            'optional_field': types.Field(types.String, is_optional=True),
                        },
                    ),
                ),
            ),
            'required_field_context':
            PipelineContextDefinition(
                context_fn=lambda *args: None,
                config_field=Field(
                    dagster_type=types.Dict(
                        fields={
                            'required_field': types.Field(types.String),
                        },
                    ),
                ),
            ),
        },
    )

    env_type = EnvironmentConfigType(pipeline_def)
    assert env_type.field_dict['solids'].is_optional
    assert env_type.field_dict['context'].is_optional is False
    context_type = env_type.field_dict['context'].dagster_type

    assert context_type.field_dict['optional_field_context'].is_optional
    assert context_type.field_dict['required_field_context'].is_optional

    assert env_type.field_dict['execution'].is_optional
    assert env_type.field_dict['expectations'].is_optional

    env_obj = throwing_evaluate_config_value(
        env_type,
        {
            'context': {
                'optional_field_context': {
                    'config': {
                        'optional_field': 'foobar',
                    },
                },
            },
        },
    )

    assert env_obj.context.name == 'optional_field_context'
    assert env_obj.context.config == {'optional_field': 'foobar'}
