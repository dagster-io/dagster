import pytest

from dagster import (
    ConfigDefinition,
    DagsterEvaluateValueError,
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
    all_optional_user_config,
    camelcase,
)


def test_camelcase():
    assert camelcase('foo') == 'Foo'
    assert camelcase('foo_bar') == 'FooBar'
    assert camelcase('foo.bar') == 'FooBar'
    assert camelcase('foo-bar') == 'FooBar'


def test_context_config_any():
    context_defs = {
        'test':
        PipelineContextDefinition(
            config_def=ConfigDefinition(),
            context_fn=lambda *args: ExecutionContext(),
        )
    }

    context_config_type = ContextConfigType('something', context_defs)
    output = context_config_type.evaluate_value({'test': {'config': 1}})
    assert output.name == 'test'
    assert output.config == 1


def test_context_config():
    context_defs = {
        'test':
        PipelineContextDefinition(
            config_def=ConfigDefinition(
                config_type=types.
                ConfigDictionary('TestConfigDict', {
                    'some_str': Field(types.String),
                })
            ),
            context_fn=lambda *args: ExecutionContext(),
        )
    }

    context_config_type = ContextConfigType('something', context_defs)

    output = context_config_type.evaluate_value({'test': {'config': {'some_str': 'something'}}})
    assert isinstance(output, config.Context)
    assert output.name == 'test'
    assert output.config == {'some_str': 'something'}


def test_memoized_context():
    context_defs = {
        'test':
        PipelineContextDefinition(
            config_def=ConfigDefinition(),
            context_fn=lambda *args: ExecutionContext(),
        )
    }

    context_config_type = ContextConfigType('something', context_defs)

    output = context_config_type.evaluate_value(config.Context(name='test', config='whatever'))
    assert isinstance(output, config.Context)
    assert output.name == 'test'
    assert output.config == 'whatever'


def test_default_expectations():
    expect_config_type = ExpectationsConfigType('some_name')
    assert expect_config_type.evaluate_value({}).evaluate is True
    assert expect_config_type.evaluate_value(None).evaluate is True


def test_default_execution():
    execution_config_type = ExecutionConfigType('some_name')
    assert execution_config_type.evaluate_value({}).serialize_intermediates is False
    assert execution_config_type.evaluate_value(None).serialize_intermediates is False


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

    assert all_optional_user_config(default_context_config_type)

    context_dict = context_config_type.evaluate_value({})

    assert 'default' in context_dict


def test_provided_default_config():
    pipeline_def = PipelineDefinition(
        context_definitions={
            'some_context':
            PipelineContextDefinition(
                config_def=ConfigDefinition(
                    config_type=types.ConfigDictionary(
                        'ksjdkfjd', {
                            'with_default_int':
                            Field(
                                types.Int,
                                is_optional=True,
                                default_value=23434,
                            ),
                        }
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
    env_obj = env_type.evaluate_value({})
    assert env_obj.context.name == 'some_context'


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
    env_obj = env_type.evaluate_value({})

    assert env_obj.expectations.evaluate is True
    assert env_obj.execution.serialize_intermediates is False


def test_errors():
    context_defs = {
        'test':
        PipelineContextDefinition(
            config_def=ConfigDefinition(
                types.ConfigDictionary(
                    'something',
                    {
                        'required_int': types.Field(types.Int),
                    },
                )
            ),
            context_fn=lambda *args: ExecutionContext(),
        )
    }

    context_config_type = ContextConfigType('something', context_defs)

    with pytest.raises(DagsterEvaluateValueError, match='must be None or dict'):
        context_config_type.evaluate_value(1)

    with pytest.raises(DagsterEvaluateValueError, match='Must specify in config'):
        context_config_type.evaluate_value({})

    # I tried doing some regular expressions here but the rules differ for escaping
    # between 2.7, 3.5, or 3.6 so gave up and did this hackneyed solution
    with pytest.raises(DagsterEvaluateValueError, match='You can only specify a single context'):
        context_config_type.evaluate_value({
            'context_one': 1,
            'context_two': 2,
        })

    with pytest.raises(DagsterEvaluateValueError, match="You specified"):
        context_config_type.evaluate_value({
            'context_one': 1,
            'context_two': 2,
        })

    with pytest.raises(DagsterEvaluateValueError, match="'context_one', 'context_two'"):
        context_config_type.evaluate_value({
            'context_one': 1,
            'context_two': 2,
        })

    with pytest.raises(DagsterEvaluateValueError, match="The available contexts are"):
        context_config_type.evaluate_value({
            'context_one': 1,
            'context_two': 2,
        })

    with pytest.raises(DagsterEvaluateValueError, match="'test'"):
        context_config_type.evaluate_value({
            'context_one': 1,
            'context_two': 2,
        })


def test_select_context():
    context_defs = {
        'int_context':
        PipelineContextDefinition(
            config_def=ConfigDefinition(types.Int),
            context_fn=lambda *args: ExecutionContext(),
        ),
        'string_context':
        PipelineContextDefinition(
            config_def=ConfigDefinition(types.String),
            context_fn=lambda *args: ExecutionContext(),
        ),
    }

    context_config_type = ContextConfigType('something', context_defs)

    assert context_config_type.evaluate_value({
        'int_context': {
            'config': 1
        },
    }) == config.Context(
        name='int_context',
        config=1,
    )

    assert context_config_type.evaluate_value({
        'string_context': {
            'config': 'bar'
        },
    }) == config.Context(
        name='string_context',
        config='bar',
    )

    # mismatched field type mismatch
    with pytest.raises(DagsterEvaluateValueError):
        assert context_config_type.evaluate_value({
            'int_context': {
                'config': 'bar'
            },
        })

    # mismatched field type mismatch
    with pytest.raises(DagsterEvaluateValueError):
        assert context_config_type.evaluate_value({
            'string_context': {
                'config': 1
            },
        })


def test_solid_config():
    solid_config_type = SolidConfigType('kdjfkd', types.Int)
    solid_inst = solid_config_type.evaluate_value({'config': 1})
    assert isinstance(solid_inst, config.Solid)
    assert solid_inst.config == 1


def test_expectations_config():
    expectations_config_type = ExpectationsConfigType('ksjdfkd')
    expectations = expectations_config_type.evaluate_value({'evaluate': True})

    assert isinstance(expectations, config.Expectations)
    assert expectations.evaluate is True

    assert expectations_config_type.evaluate_value({
        'evaluate': False
    }) == config.Expectations(evaluate=False)


def test_solid_dictionary_type():
    pipeline_def = define_test_solids_config_pipeline()

    solid_dict_type = SolidDictionaryType('foobar', pipeline_def)

    value = solid_dict_type.evaluate_value(
        {
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


def define_test_solids_config_pipeline():
    return PipelineDefinition(
        solids=[
            SolidDefinition(
                name='int_config_solid',
                config_def=ConfigDefinition(types.Int),
                inputs=[],
                outputs=[],
                transform_fn=lambda *args: None,
            ),
            SolidDefinition(
                name='string_config_solid',
                config_def=ConfigDefinition(types.String),
                inputs=[],
                outputs=[],
                transform_fn=lambda *args: None,
            )
        ]
    )


def test_solid_dictionary_some_no_config():
    pipeline_def = PipelineDefinition(
        solids=[
            SolidDefinition(
                name='int_config_solid',
                config_def=ConfigDefinition(types.Int),
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

    value = solid_dict_type.evaluate_value({
        'int_config_solid': {
            'config': 1,
        },
    })

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
                config_def=ConfigDefinition(),
                context_fn=lambda *args: ExecutionContext(),
            )
        },
        solids=[
            SolidDefinition(
                name='int_config_solid',
                config_def=ConfigDefinition(types.Int),
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
                                  ].dagster_type.name == 'SomePipeline.IntConfigSolid.SolidConfig'
    assert environment_type.field_dict['expectations'
                                       ].dagster_type.name == 'SomePipeline.ExpectationsConfig'

    env = environment_type.evaluate_value(
        {
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

    with pytest.raises(DagsterEvaluateValueError, match='Field notconfig not found.'):
        int_solid_config.evaluate_value({'notconfig': 1})

    with pytest.raises(DagsterEvaluateValueError):
        int_solid_config.evaluate_value(1)


def test_execution_config():
    env_type = EnvironmentConfigType(define_test_solids_config_pipeline())
    env_obj = env_type.evaluate_value({'execution': {'serialize_intermediates': True}})
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
                config_def=ConfigDefinition(types.Int),
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

    env_type = EnvironmentConfigType(pipeline_def)
    env_obj = env_type.evaluate_value({'solids': {'int_config_solid': {'config': 234}}})

    assert env_obj.solids['int_config_solid'].config == 234

    assert execute_pipeline(pipeline_def, env_obj).success


def test_optional_solid_with_optional_scalar_config():
    def _assert_config_none(info, value):
        assert info.config is value

    pipeline_def = PipelineDefinition(
        name='some_pipeline',
        solids=[
            SolidDefinition(
                name='int_config_solid',
                config_def=ConfigDefinition(types.Int),
                inputs=[],
                outputs=[],
                transform_fn=lambda info, _inputs: _assert_config_none(info, 234),
            ),
        ]
    )

    env_type = EnvironmentConfigType(pipeline_def)

    assert env_type.field_dict['solids'].is_optional is True

    solids_type = env_type.field_dict['solids'].dagster_type

    assert solids_type.field_dict['int_config_solid'].is_optional is True

    solids_default_obj = solids_type.evaluate_value({})

    assert solids_default_obj['int_config_solid'].config is None

    env_obj = env_type.evaluate_value({})

    assert env_obj.solids['int_config_solid'].config is None


def test_required_solid_with_required_subfield():
    pipeline_def = PipelineDefinition(
        name='some_pipeline',
        solids=[
            SolidDefinition(
                name='int_config_solid',
                config_def=ConfigDefinition(
                    types.ConfigDictionary(
                        'TestRequiredSolidConfig',
                        {
                            'required_field': types.Field(types.String),
                        },
                    )
                ),
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

    env_obj = env_type.evaluate_value(
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

    with pytest.raises(DagsterEvaluateValueError):
        env_type.evaluate_value({'solids': {}})

    with pytest.raises(DagsterEvaluateValueError):
        env_type.evaluate_value({})


def test_optional_solid_with_optional_subfield():
    pipeline_def = PipelineDefinition(
        name='some_pipeline',
        solids=[
            SolidDefinition(
                name='int_config_solid',
                config_def=ConfigDefinition(
                    types.ConfigDictionary(
                        'TestOptionalSolidConfig', {
                            'optional_field': types.Field(types.String, is_optional=True),
                        }
                    )
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
                config_def=ConfigDefinition(
                    config_type=types.ConfigDictionary(
                        name='some_context_config',
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
                config_def=ConfigDefinition(
                    config_type=types.ConfigDictionary(
                        name='some_context_config',
                        fields={
                            'optional_field': types.Field(types.String, is_optional=True),
                        },
                    ),
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
                config_def=ConfigDefinition(
                    config_type=types.ConfigDictionary(
                        name='some_optional_context_config',
                        fields={
                            'optional_field': types.Field(types.String, is_optional=True),
                        },
                    ),
                ),
            ),
            'required_field_context':
            PipelineContextDefinition(
                context_fn=lambda *args: None,
                config_def=ConfigDefinition(
                    config_type=types.ConfigDictionary(
                        name='some_required_context_config',
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

    env_obj = env_type.evaluate_value(
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


def test_default_optional_and_required_context():
    pipeline_def = PipelineDefinition(
        name='some_pipeline',
        solids=[],
        context_definitions={
            'default':
            PipelineContextDefinition(
                context_fn=lambda *args: None,
                config_def=ConfigDefinition(
                    config_type=types.ConfigDictionary(
                        name='some_optional_context_config',
                        fields={
                            'optional_field': types.Field(types.String, is_optional=True),
                        },
                    ),
                ),
            ),
            'required_field_context':
            PipelineContextDefinition(
                context_fn=lambda *args: None,
                config_def=ConfigDefinition(
                    config_type=types.ConfigDictionary(
                        name='some_required_context_config',
                        fields={
                            'required_field': types.Field(types.String),
                        },
                    ),
                ),
            ),
        },
    )

    env_type = EnvironmentConfigType(pipeline_def)
    assert env_type.field_dict['context'].is_optional

    env_obj = env_type.evaluate_value({})
    assert env_obj.context.name == 'default'
    assert env_obj.context.config == {}


def test_default_optional_with_default_value_and_required_context():
    pipeline_def = PipelineDefinition(
        name='some_pipeline',
        solids=[],
        context_definitions={
            'default':
            PipelineContextDefinition(
                context_fn=lambda *args: None,
                config_def=ConfigDefinition(
                    config_type=types.ConfigDictionary(
                        name='some_optional_context_config',
                        fields={
                            'optional_field':
                            types.Field(
                                types.String,
                                is_optional=True,
                                default_value='foobar',
                            ),
                        },
                    ),
                ),
            ),
            'required_field_context':
            PipelineContextDefinition(
                context_fn=lambda *args: None,
                config_def=ConfigDefinition(
                    config_type=types.ConfigDictionary(
                        name='some_required_context_config',
                        fields={
                            'required_field': types.Field(types.String),
                        },
                    ),
                ),
            ),
        },
    )

    env_type = EnvironmentConfigType(pipeline_def)
    assert env_type.field_dict['context'].is_optional

    env_obj = env_type.evaluate_value({})
    assert env_obj.context.name == 'default'
    assert env_obj.context.config == {'optional_field': 'foobar'}
