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
)

from dagster.core.config_types import (
    ContextConfigType,
    EnvironmentConfigType,
    ExpectationsConfigType,
    SolidConfigType,
    SolidDictionaryType,
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


def test_errors():
    context_defs = {
        'test':
        PipelineContextDefinition(
            config_def=ConfigDefinition(),
            context_fn=lambda *args: ExecutionContext(),
        )
    }

    context_config_type = ContextConfigType('something', context_defs)

    with pytest.raises(DagsterEvaluateValueError, match='must be dict'):
        context_config_type.evaluate_value(1)

    with pytest.raises(DagsterEvaluateValueError, match='Must specify a context'):
        context_config_type.evaluate_value({})

    with pytest.raises(DagsterEvaluateValueError, match='You can only specify a single context'):
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

    with pytest.raises(DagsterEvaluateValueError):
        assert context_config_type.evaluate_value({
            'int_context': {
                'config': 'bar'
            },
        })

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
