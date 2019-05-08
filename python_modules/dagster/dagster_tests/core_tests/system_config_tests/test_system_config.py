import pytest

from dagster import (
    Any,
    DagsterEvaluateConfigValueError,
    DependencyDefinition,
    Dict,
    ExecutionContext,
    Field,
    InputDefinition,
    Int,
    NamedDict,
    OutputDefinition,
    PipelineContextDefinition,
    PipelineDefinition,
    SolidDefinition,
    SolidInstance,
    String,
    execute_pipeline,
    lambda_solid,
    types,
)


from dagster.core.system_config.objects import (
    ContextConfig,
    EnvironmentConfig,
    ExpectationsConfig,
    SolidConfig,
)

from dagster.core.definitions import create_environment_type, create_environment_schema

from dagster.core.definitions.environment_configs import (
    construct_context_config,
    construct_environment_config,
    construct_solid_dictionary,
    define_context_context_cls,
    define_expectations_config_cls,
    define_solid_config_cls,
    define_solid_dictionary_cls,
    EnvironmentClassCreationData,
)

from dagster.core.types.evaluator import evaluate_config_value

from dagster.core.test_utils import throwing_evaluate_config_value


def create_creation_data(pipeline_def):
    return EnvironmentClassCreationData(
        pipeline_def.name,
        pipeline_def.solids,
        pipeline_def.context_definitions,
        pipeline_def.dependency_structure,
    )


def test_context_config_any():
    context_defs = {
        'test': PipelineContextDefinition(
            config_field=Field(Any), context_fn=lambda *args: ExecutionContext()
        )
    }

    context_config_type = define_context_context_cls('something', context_defs).inst()

    assert context_config_type.type_attributes.is_system_config

    output = construct_context_config(
        throwing_evaluate_config_value(context_config_type, {'test': {'config': 1}})
    )
    assert output.name == 'test'
    assert output.config == 1


def test_context_config():
    context_defs = {
        'test': PipelineContextDefinition(
            config_field=Field(dagster_type=Dict({'some_str': Field(String)})),
            context_fn=lambda *args: ExecutionContext(),
        )
    }

    context_config_type = define_context_context_cls('something', context_defs).inst()

    output = construct_context_config(
        throwing_evaluate_config_value(
            context_config_type, {'test': {'config': {'some_str': 'something'}}}
        )
    )
    assert isinstance(output, ContextConfig)
    assert output.name == 'test'
    assert output.config == {'some_str': 'something'}


def test_default_expectations():
    expect_config_type = define_expectations_config_cls('some_name').inst()
    assert (
        ExpectationsConfig(**throwing_evaluate_config_value(expect_config_type, {})).evaluate
        is True
    )
    assert (
        ExpectationsConfig(**throwing_evaluate_config_value(expect_config_type, None)).evaluate
        is True
    )


def test_default_context_config():
    pipeline_def = PipelineDefinition(
        solids=[
            SolidDefinition(
                name='some_solid', inputs=[], outputs=[], transform_fn=lambda *args: None
            )
        ]
    )

    context_config_type = define_context_context_cls(
        pipeline_def.name, pipeline_def.context_definitions
    ).inst()
    assert 'default' in context_config_type.fields
    assert context_config_type.fields['default'].is_optional
    default_context_config_type = context_config_type.fields['default'].config_type

    assert 'config' in default_context_config_type.fields

    context_dict = throwing_evaluate_config_value(context_config_type, {})

    assert 'default' in context_dict


def test_all_types_provided():
    pipeline_def = PipelineDefinition(
        name='pipeline',
        solids=[],
        context_definitions={
            'some_context': PipelineContextDefinition(
                config_field=Field(
                    NamedDict(
                        'SomeContextNamedDict',
                        {'with_default_int': Field(Int, is_optional=True, default_value=23434)},
                    )
                ),
                context_fn=lambda *args: None,
            )
        },
    )

    environment_schema = create_environment_schema(pipeline_def)

    all_types = list(environment_schema.all_config_types())
    type_names = set(t.name for t in all_types)
    assert 'SomeContextNamedDict' in type_names
    assert 'Pipeline.ContextDefinitionConfig.SomeContext' in type_names
    assert 'Pipeline.ContextDefinitionConfig.SomeContext.Resources' in type_names


def test_provided_default_config():
    pipeline_def = PipelineDefinition(
        context_definitions={
            'some_context': PipelineContextDefinition(
                config_field=Field(
                    Dict({'with_default_int': Field(Int, is_optional=True, default_value=23434)})
                ),
                context_fn=lambda *args: None,
            )
        },
        solids=[
            SolidDefinition(
                name='some_solid', inputs=[], outputs=[], transform_fn=lambda *args: None
            )
        ],
    )

    env_type = create_environment_type(pipeline_def)
    some_context_field = env_type.fields['context'].config_type.fields['some_context']
    assert some_context_field.is_optional

    some_context_config_field = some_context_field.config_type.fields['config']
    assert some_context_config_field.is_optional
    assert some_context_config_field.default_value == {'with_default_int': 23434}

    assert some_context_field.default_value == {
        'config': {'with_default_int': 23434},
        'resources': {},
        'persistence': {'file': {}},
    }

    value = construct_environment_config(throwing_evaluate_config_value(env_type, {}))
    assert value.context.name == 'some_context'
    assert env_type.type_attributes.is_system_config


def test_default_environment():
    pipeline_def = PipelineDefinition(
        solids=[
            SolidDefinition(
                name='some_solid', inputs=[], outputs=[], transform_fn=lambda *args: None
            )
        ]
    )

    env_obj = construct_environment_config(
        throwing_evaluate_config_value(create_environment_type(pipeline_def), {})
    )

    assert env_obj.expectations.evaluate is True


def test_errors():
    context_defs = {
        'test': PipelineContextDefinition(
            config_field=Field(Dict({'required_int': Field(Int)})),
            context_fn=lambda *args: ExecutionContext(),
        )
    }

    context_config_type = define_context_context_cls('something', context_defs).inst()

    assert not evaluate_config_value(context_config_type, 1).success
    assert not evaluate_config_value(context_config_type, {}).success

    invalid_value = {'context_one': 1, 'context_two': 2}

    result = evaluate_config_value(context_config_type, invalid_value)
    assert not result.success
    assert len(result.errors) == 1


def test_select_context():
    context_defs = {
        'int_context': PipelineContextDefinition(
            config_field=Field(Int), context_fn=lambda *args: ExecutionContext()
        ),
        'string_context': PipelineContextDefinition(
            config_field=Field(String), context_fn=lambda *args: ExecutionContext()
        ),
    }

    context_config_type = define_context_context_cls('something', context_defs).inst()

    assert construct_context_config(
        throwing_evaluate_config_value(context_config_type, {'int_context': {'config': 1}})
    ) == ContextConfig(name='int_context', config=1)

    assert construct_context_config(
        throwing_evaluate_config_value(context_config_type, {'string_context': {'config': 'bar'}})
    ) == ContextConfig(name='string_context', config='bar')

    # mismatched field type mismatch
    with pytest.raises(DagsterEvaluateConfigValueError):
        assert throwing_evaluate_config_value(
            context_config_type, {'int_context': {'config': 'bar'}}
        )

    # mismatched field type mismatch
    with pytest.raises(DagsterEvaluateConfigValueError):
        assert throwing_evaluate_config_value(
            context_config_type, {'string_context': {'config': 1}}
        )


def test_solid_config():
    solid_config_type = define_solid_config_cls('kdjfkd', Field(Int), None, None).inst()
    solid_inst = throwing_evaluate_config_value(solid_config_type, {'config': 1})
    assert solid_inst['config'] == 1
    assert solid_config_type.inst().type_attributes.is_system_config


def test_expectations_config():
    expectations_config_type = define_expectations_config_cls('ksjdfkd').inst()
    expectations = ExpectationsConfig(
        **throwing_evaluate_config_value(expectations_config_type, {'evaluate': True})
    )

    assert isinstance(expectations, ExpectationsConfig)
    assert expectations.evaluate is True

    assert ExpectationsConfig(
        **throwing_evaluate_config_value(expectations_config_type, {'evaluate': False})
    ) == ExpectationsConfig(evaluate=False)


def test_solid_dictionary_type():
    pipeline_def = define_test_solids_config_pipeline()

    solid_dict_type = define_solid_dictionary_cls(
        'foobar', create_creation_data(pipeline_def)
    ).inst()

    value = construct_solid_dictionary(
        throwing_evaluate_config_value(
            solid_dict_type,
            {'int_config_solid': {'config': 1}, 'string_config_solid': {'config': 'bar'}},
        )
    )

    assert set(['int_config_solid', 'string_config_solid']) == set(value.keys())
    assert value == {'int_config_solid': SolidConfig(1), 'string_config_solid': SolidConfig('bar')}

    assert solid_dict_type.type_attributes.is_system_config

    for specific_solid_config_field in solid_dict_type.fields.values():
        specific_solid_config_type = specific_solid_config_field.config_type
        assert specific_solid_config_type.type_attributes.is_system_config
        user_config_field = specific_solid_config_field.config_type.fields['config']
        assert user_config_field.config_type.type_attributes.is_system_config is False


def define_test_solids_config_pipeline():
    return PipelineDefinition(
        solids=[
            SolidDefinition(
                name='int_config_solid',
                config_field=Field(Int, is_optional=True),
                inputs=[],
                outputs=[],
                transform_fn=lambda *args: None,
            ),
            SolidDefinition(
                name='string_config_solid',
                config_field=Field(String, is_optional=True),
                inputs=[],
                outputs=[],
                transform_fn=lambda *args: None,
            ),
        ]
    )


def assert_has_fields(dtype, *fields):
    return set(dtype.fields.keys()) == set(fields)


def test_solid_configs_defaults():
    env_type = create_environment_type(define_test_solids_config_pipeline())

    solids_field = env_type.fields['solids']

    assert_has_fields(solids_field.config_type, 'int_config_solid', 'string_config_solid')

    int_solid_field = solids_field.config_type.fields['int_config_solid']

    assert int_solid_field.is_optional
    # TODO: this is the test case the exposes the default dodginess
    assert int_solid_field.default_provided

    assert_has_fields(int_solid_field.config_type, 'config')

    int_solid_config_field = int_solid_field.config_type.fields['config']

    assert int_solid_config_field.is_optional
    assert not int_solid_config_field.default_provided


def test_solid_dictionary_some_no_config():
    pipeline_def = PipelineDefinition(
        solids=[
            SolidDefinition(
                name='int_config_solid',
                config_field=Field(Int),
                inputs=[],
                outputs=[],
                transform_fn=lambda *args: None,
            ),
            SolidDefinition(
                name='no_config_solid', inputs=[], outputs=[], transform_fn=lambda *args: None
            ),
        ]
    )

    solid_dict_type = define_solid_dictionary_cls(
        'foobar', create_creation_data(pipeline_def)
    ).inst()

    value = construct_solid_dictionary(
        throwing_evaluate_config_value(solid_dict_type, {'int_config_solid': {'config': 1}})
    )

    assert set(['int_config_solid']) == set(value.keys())
    assert value == {'int_config_solid': SolidConfig(1)}


def test_whole_environment():
    pipeline_def = PipelineDefinition(
        name='some_pipeline',
        context_definitions={
            'test': PipelineContextDefinition(
                config_field=Field(Any), context_fn=lambda *args: ExecutionContext()
            )
        },
        solids=[
            SolidDefinition(
                name='int_config_solid',
                config_field=Field(Int),
                inputs=[],
                outputs=[],
                transform_fn=lambda *args: None,
            ),
            SolidDefinition(
                name='no_config_solid', inputs=[], outputs=[], transform_fn=lambda *args: None
            ),
        ],
    )

    environment_type = create_environment_type(pipeline_def)

    assert environment_type.fields['context'].config_type.name == 'SomePipeline.ContextConfig'
    solids_type = environment_type.fields['solids'].config_type
    assert solids_type.name == 'SomePipeline.SolidsConfigDictionary'
    assert (
        solids_type.fields['int_config_solid'].config_type.name
        == 'SomePipeline.SolidConfig.IntConfigSolid'
    )
    assert (
        environment_type.fields['expectations'].config_type.name
        == 'SomePipeline.ExpectationsConfig'
    )

    env = construct_environment_config(
        throwing_evaluate_config_value(
            environment_type,
            {'context': {'test': {'config': 1}}, 'solids': {'int_config_solid': {'config': 123}}},
        )
    )

    assert isinstance(env, EnvironmentConfig)
    assert env.context == ContextConfig('test', 1, persistence={'file': {}})
    assert env.solids == {'int_config_solid': SolidConfig(123)}
    assert env.expectations == ExpectationsConfig(evaluate=True)


def test_solid_config_error():
    solid_dict_type = define_solid_dictionary_cls(
        'slkdfjkjdsf', create_creation_data(define_test_solids_config_pipeline())
    ).inst()

    int_solid_config_type = solid_dict_type.fields['int_config_solid'].config_type

    with pytest.raises(DagsterEvaluateConfigValueError, match='Field "notconfig" is not defined'):
        throwing_evaluate_config_value(int_solid_config_type, {'notconfig': 1})

    with pytest.raises(DagsterEvaluateConfigValueError):
        throwing_evaluate_config_value(int_solid_config_type, 1)


def test_optional_solid_with_no_config():
    def _assert_config_none(context, value):
        assert context.solid_config is value

    pipeline_def = PipelineDefinition(
        name='some_pipeline',
        solids=[
            SolidDefinition(
                name='int_config_solid',
                config_field=Field(Int),
                inputs=[],
                outputs=[],
                transform_fn=lambda context, _inputs: _assert_config_none(context, 234),
            ),
            SolidDefinition(
                name='no_config_solid',
                inputs=[],
                outputs=[],
                transform_fn=lambda context, _inputs: _assert_config_none(context, None),
            ),
        ],
    )

    assert execute_pipeline(pipeline_def, {'solids': {'int_config_solid': {'config': 234}}}).success


def test_optional_solid_with_optional_scalar_config():
    def _assert_config_none(context, value):
        assert context.solid_config is value

    pipeline_def = PipelineDefinition(
        name='some_pipeline',
        solids=[
            SolidDefinition(
                name='int_config_solid',
                config_field=Field(Int, is_optional=True),
                inputs=[],
                outputs=[],
                transform_fn=lambda context, _inputs: _assert_config_none(context, 234),
            )
        ],
    )

    env_type = create_environment_type(pipeline_def)

    assert env_type.fields['solids'].is_optional is True

    solids_type = env_type.fields['solids'].config_type

    assert solids_type.fields['int_config_solid'].is_optional is True

    solids_default_obj = construct_solid_dictionary(throwing_evaluate_config_value(solids_type, {}))

    assert solids_default_obj['int_config_solid'].config is None

    env_obj = construct_environment_config(throwing_evaluate_config_value(env_type, {}))

    assert env_obj.solids['int_config_solid'].config is None


def test_optional_solid_with_required_scalar_config():
    def _assert_config_none(context, value):
        assert context.solid_config is value

    pipeline_def = PipelineDefinition(
        name='some_pipeline',
        solids=[
            SolidDefinition(
                name='int_config_solid',
                config_field=Field(Int),
                inputs=[],
                outputs=[],
                transform_fn=lambda context, _inputs: _assert_config_none(context, 234),
            )
        ],
    )

    env_type = create_environment_type(pipeline_def)

    assert env_type.fields['solids'].is_optional is False

    solids_type = env_type.fields['solids'].config_type

    assert solids_type.fields['int_config_solid'].is_optional is False

    int_config_solid_type = solids_type.fields['int_config_solid'].config_type

    assert_has_fields(int_config_solid_type, 'config')

    int_config_solid_config_field = int_config_solid_type.fields['config']

    assert int_config_solid_config_field.is_optional is False

    execute_pipeline(pipeline_def, {'solids': {'int_config_solid': {'config': 234}}})


def test_required_solid_with_required_subfield():
    pipeline_def = PipelineDefinition(
        name='some_pipeline',
        solids=[
            SolidDefinition(
                name='int_config_solid',
                config_field=Field(Dict({'required_field': Field(String)})),
                inputs=[],
                outputs=[],
                transform_fn=lambda *_args: None,
            )
        ],
    )

    env_type = create_environment_type(pipeline_def)

    assert env_type.fields['solids'].is_optional is False
    assert env_type.fields['solids'].config_type

    solids_type = env_type.fields['solids'].config_type
    assert solids_type.fields['int_config_solid'].is_optional is False
    int_config_solid_type = solids_type.fields['int_config_solid'].config_type
    assert int_config_solid_type.fields['config'].is_optional is False

    assert env_type.fields['context'].is_optional
    assert env_type.fields['execution'].is_optional
    assert env_type.fields['expectations'].is_optional

    env_obj = construct_environment_config(
        throwing_evaluate_config_value(
            env_type, {'solids': {'int_config_solid': {'config': {'required_field': 'foobar'}}}}
        )
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
                    Dict({'optional_field': Field(String, is_optional=True)}), is_optional=True
                ),
                inputs=[],
                outputs=[],
                transform_fn=lambda *_args: None,
            )
        ],
    )

    env_type = create_environment_type(pipeline_def)
    assert env_type.fields['solids'].is_optional
    assert env_type.fields['context'].is_optional
    assert env_type.fields['execution'].is_optional
    assert env_type.fields['expectations'].is_optional


def test_required_context_with_required_subfield():
    pipeline_def = PipelineDefinition(
        name='some_pipeline',
        solids=[],
        context_definitions={
            'some_context': PipelineContextDefinition(
                context_fn=lambda *args: None,
                config_field=Field(Dict({'required_field': Field(String)})),
            )
        },
    )

    env_type = create_environment_type(pipeline_def)
    assert env_type.fields['solids'].is_optional
    assert env_type.fields['context'].is_optional is False
    assert env_type.fields['execution'].is_optional
    assert env_type.fields['expectations'].is_optional

    context_union_config_type = env_type.fields['context'].config_type
    assert context_union_config_type.fields['some_context'].is_optional is False


def test_all_optional_field_on_single_context_dict():
    pipeline_def = PipelineDefinition(
        name='some_pipeline',
        solids=[],
        context_definitions={
            'some_context': PipelineContextDefinition(
                context_fn=lambda *args: None,
                config_field=Field(Dict({'optional_field': Field(String, is_optional=True)})),
            )
        },
    )

    env_type = create_environment_type(pipeline_def)
    assert env_type.fields['solids'].is_optional
    assert env_type.fields['context'].is_optional
    assert env_type.fields['execution'].is_optional
    assert env_type.fields['expectations'].is_optional


def test_optional_and_required_context():
    pipeline_def = PipelineDefinition(
        name='some_pipeline',
        solids=[],
        context_definitions={
            'optional_field_context': PipelineContextDefinition(
                context_fn=lambda *args: None,
                config_field=Field(
                    dagster_type=Dict(fields={'optional_field': Field(String, is_optional=True)})
                ),
            ),
            'required_field_context': PipelineContextDefinition(
                context_fn=lambda *args: None,
                config_field=Field(dagster_type=Dict(fields={'required_field': Field(String)})),
            ),
        },
    )

    env_type = create_environment_type(pipeline_def)
    assert env_type.fields['solids'].is_optional
    assert env_type.fields['context'].is_optional is False
    context_type = env_type.fields['context'].config_type

    assert context_type.fields['optional_field_context'].is_optional
    assert context_type.fields['required_field_context'].is_optional

    assert env_type.fields['execution'].is_optional
    assert env_type.fields['expectations'].is_optional

    env_obj = construct_environment_config(
        throwing_evaluate_config_value(
            env_type,
            {'context': {'optional_field_context': {'config': {'optional_field': 'foobar'}}}},
        )
    )

    assert env_obj.context.name == 'optional_field_context'
    assert env_obj.context.config == {'optional_field': 'foobar'}


def test_required_inputs():
    @lambda_solid(inputs=[InputDefinition('num', types.Int)], output=OutputDefinition(types.Int))
    def add_one(num):
        return num + 1

    pipeline_def = PipelineDefinition(
        name='required_int_input',
        solids=[add_one],
        dependencies={
            SolidInstance('add_one', 'first_add'): {},
            SolidInstance('add_one', 'second_add'): {'num': DependencyDefinition('first_add')},
        },
    )

    env_type = create_environment_type(pipeline_def)

    solids_type = env_type.fields['solids'].config_type

    first_add_fields = solids_type.fields['first_add'].config_type.fields

    assert 'inputs' in first_add_fields

    inputs_field = first_add_fields['inputs']

    assert inputs_field.is_required

    assert inputs_field.config_type.fields['num'].is_required

    # second_add has a dependency so the input is not available
    assert 'inputs' not in solids_type.fields['second_add'].config_type.fields


def test_mix_required_inputs():
    @lambda_solid(
        inputs=[InputDefinition('left', types.Int), InputDefinition('right', types.Int)],
        output=OutputDefinition(types.Int),
    )
    def add_numbers(left, right):
        return left + right

    @lambda_solid
    def return_three():
        return 3

    pipeline_def = PipelineDefinition(
        name='mixed_required_inputs',
        solids=[add_numbers, return_three],
        dependencies={'add_numbers': {'right': DependencyDefinition('return_three')}},
    )

    env_type = create_environment_type(pipeline_def)
    solids_type = env_type.fields['solids'].config_type
    add_numbers_type = solids_type.fields['add_numbers'].config_type
    inputs_fields_dict = add_numbers_type.fields['inputs'].config_type.fields

    assert 'left' in inputs_fields_dict
    assert not 'right' in inputs_fields_dict


def test_files_default_config():
    pipeline_def = PipelineDefinition(name='pipeline', solids=[])

    env_type = create_environment_type(pipeline_def)
    assert 'storage' in env_type.fields

    config_value = throwing_evaluate_config_value(env_type, {})

    assert 'storage' not in config_value


def test_storage_in_memory_config():
    pipeline_def = PipelineDefinition(name='pipeline', solids=[])

    env_type = create_environment_type(pipeline_def)
    assert 'storage' in env_type.fields

    config_value = throwing_evaluate_config_value(env_type, {'storage': {'in_memory': {}}})

    assert config_value['storage'] == {'in_memory': {}}
