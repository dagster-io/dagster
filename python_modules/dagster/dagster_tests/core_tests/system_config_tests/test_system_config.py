import pytest

from dagster import (
    Any,
    DependencyDefinition,
    Dict,
    Field,
    InputDefinition,
    Int,
    ModeDefinition,
    NamedDict,
    OutputDefinition,
    ResourceDefinition,
    PipelineDefinition,
    SolidDefinition,
    SolidInvocation,
    String,
    execute_pipeline,
    lambda_solid,
)
from dagster.core.definitions import create_environment_type, create_environment_schema
from dagster.core.definitions.environment_configs import (
    define_resource_cls,
    define_expectations_config_cls,
    define_solid_config_cls,
    define_solid_dictionary_cls,
    EnvironmentClassCreationData,
)
from dagster.core.types.evaluator.errors import DagsterEvaluateConfigValueError
from dagster.core.system_config.objects import (
    construct_solid_dictionary,
    EnvironmentConfig,
    ExpectationsConfig,
    SolidConfig,
)
from dagster.core.test_utils import throwing_evaluate_config_value
from dagster.core.types.evaluator import evaluate_config
from dagster.loggers import default_loggers


def create_creation_data(pipeline_def):
    return EnvironmentClassCreationData(
        pipeline_def.name,
        pipeline_def.solids,
        pipeline_def.dependency_structure,
        mode_definition=None,
        logger_defs=default_loggers(),
    )


def test_resource_config_any():
    resource_type = define_resource_cls(
        'Parent', 'Foo', ResourceDefinition(lambda: None, Field(Any))
    ).inst()

    assert resource_type.type_attributes.is_system_config

    assert throwing_evaluate_config_value(resource_type, {'config': 1}) == {'config': 1}


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


def test_all_types_provided():
    pipeline_def = PipelineDefinition(
        name='pipeline',
        solid_defs=[],
        mode_defs=[
            ModeDefinition(
                name='SomeMode',
                resource_defs={
                    'some_resource': ResourceDefinition(
                        lambda: None,
                        config_field=Field(
                            NamedDict(
                                'SomeModeNamedDict',
                                {
                                    'with_default_int': Field(
                                        Int, is_optional=True, default_value=23434
                                    )
                                },
                            )
                        ),
                    )
                },
            )
        ],
    )

    environment_schema = create_environment_schema(pipeline_def)

    all_types = list(environment_schema.all_config_types())
    type_names = set(t.name for t in all_types)
    assert 'SomeModeNamedDict' in type_names
    assert 'Pipeline.Mode.SomeMode.Environment' in type_names
    assert 'Pipeline.Mode.SomeMode.Resources.SomeResource' in type_names


def test_provided_default_on_resources_config():
    pipeline_def = PipelineDefinition(
        mode_defs=[
            ModeDefinition(
                name='some_mode',
                resource_defs={
                    'some_resource': ResourceDefinition(
                        resource_fn=lambda: None,
                        config_field=Field(
                            Dict(
                                {
                                    'with_default_int': Field(
                                        Int, is_optional=True, default_value=23434
                                    )
                                }
                            )
                        ),
                    )
                },
            )
        ],
        solid_defs=[
            SolidDefinition(
                name='some_solid', input_defs=[], output_defs=[], compute_fn=lambda *args: None
            )
        ],
    )

    env_type = create_environment_type(pipeline_def)
    assert env_type.type_attributes.is_system_config
    some_resource_field = env_type.fields['resources'].config_type.fields['some_resource']
    assert some_resource_field.is_optional

    some_resource_config_field = some_resource_field.config_type.fields['config']
    assert some_resource_config_field.is_optional
    assert some_resource_config_field.default_value == {'with_default_int': 23434}

    assert some_resource_field.default_value == {'config': {'with_default_int': 23434}}

    value = EnvironmentConfig.from_dict(throwing_evaluate_config_value(env_type, {}))
    assert value.resources == {'some_resource': {'config': {'with_default_int': 23434}}}


def test_default_environment():
    pipeline_def = PipelineDefinition(
        solid_defs=[
            SolidDefinition(
                name='some_solid', input_defs=[], output_defs=[], compute_fn=lambda *args: None
            )
        ]
    )

    env_obj = EnvironmentConfig.from_dict(
        throwing_evaluate_config_value(create_environment_type(pipeline_def), {})
    )

    assert env_obj.expectations.evaluate is True


def test_resource_def_config_errors():
    takes_int_resource_def = ResourceDefinition(
        resource_fn=lambda: None, config_field=Field(Dict({'required_int': Field(Int)}))
    )

    resource_type = define_resource_cls('Parent', 'takes_int', takes_int_resource_def).inst()

    assert not evaluate_config(resource_type, 1).success
    assert not evaluate_config(resource_type, {}).success
    assert not evaluate_config(resource_type, {'config': {}}).success
    assert evaluate_config(resource_type, {'config': {'required_int': 2}}).success
    assert not evaluate_config(resource_type, {'config': {'required_int': 'kdjfkd'}}).success


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
        'foobar', pipeline_def.solids, pipeline_def.dependency_structure, pipeline_def.name
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
        solid_defs=[
            SolidDefinition(
                name='int_config_solid',
                config_field=Field(Int, is_optional=True),
                input_defs=[],
                output_defs=[],
                compute_fn=lambda *args: None,
            ),
            SolidDefinition(
                name='string_config_solid',
                config_field=Field(String, is_optional=True),
                input_defs=[],
                output_defs=[],
                compute_fn=lambda *args: None,
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
        solid_defs=[
            SolidDefinition(
                name='int_config_solid',
                config_field=Field(Int),
                input_defs=[],
                output_defs=[],
                compute_fn=lambda *args: None,
            ),
            SolidDefinition(
                name='no_config_solid', input_defs=[], output_defs=[], compute_fn=lambda *args: None
            ),
        ]
    )

    solid_dict_type = define_solid_dictionary_cls(
        'foobar', pipeline_def.solids, pipeline_def.dependency_structure, pipeline_def.name
    ).inst()

    value = construct_solid_dictionary(
        throwing_evaluate_config_value(solid_dict_type, {'int_config_solid': {'config': 1}})
    )

    assert set(['int_config_solid']) == set(value.keys())
    assert value == {'int_config_solid': SolidConfig(1)}


def test_whole_environment():
    pipeline_def = PipelineDefinition(
        name='some_pipeline',
        mode_defs=[
            ModeDefinition(
                name='test_mode',
                resource_defs={
                    'test_resource': ResourceDefinition(
                        resource_fn=lambda: None, config_field=Field(Any)
                    )
                },
            )
        ],
        solid_defs=[
            SolidDefinition(
                name='int_config_solid',
                config_field=Field(Int),
                input_defs=[],
                output_defs=[],
                compute_fn=lambda *args: None,
            ),
            SolidDefinition(
                name='no_config_solid', input_defs=[], output_defs=[], compute_fn=lambda *args: None
            ),
        ],
    )

    environment_type = create_environment_type(pipeline_def)

    assert (
        environment_type.fields['resources'].config_type.name
        == 'SomePipeline.Mode.TestMode.Resources'
    )
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

    env = EnvironmentConfig.from_dict(
        throwing_evaluate_config_value(
            environment_type,
            {
                'resources': {'test_resource': {'config': 1}},
                'solids': {'int_config_solid': {'config': 123}},
            },
        )
    )

    assert isinstance(env, EnvironmentConfig)
    assert env.solids == {'int_config_solid': SolidConfig(123)}
    assert env.expectations == ExpectationsConfig(evaluate=True)
    assert env.resources == {'test_resource': {'config': 1}}


def test_solid_config_error():
    pipeline_def = define_test_solids_config_pipeline()
    solid_dict_type = define_solid_dictionary_cls(
        'slkdfjkjdsf', pipeline_def.solids, pipeline_def.dependency_structure, pipeline_def.name
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
        solid_defs=[
            SolidDefinition(
                name='int_config_solid',
                config_field=Field(Int),
                input_defs=[],
                output_defs=[],
                compute_fn=lambda context, _inputs: _assert_config_none(context, 234),
            ),
            SolidDefinition(
                name='no_config_solid',
                input_defs=[],
                output_defs=[],
                compute_fn=lambda context, _inputs: _assert_config_none(context, None),
            ),
        ],
    )

    assert execute_pipeline(pipeline_def, {'solids': {'int_config_solid': {'config': 234}}}).success


def test_optional_solid_with_optional_scalar_config():
    def _assert_config_none(context, value):
        assert context.solid_config is value

    pipeline_def = PipelineDefinition(
        name='some_pipeline',
        solid_defs=[
            SolidDefinition(
                name='int_config_solid',
                config_field=Field(Int, is_optional=True),
                input_defs=[],
                output_defs=[],
                compute_fn=lambda context, _inputs: _assert_config_none(context, 234),
            )
        ],
    )

    env_type = create_environment_type(pipeline_def)

    assert env_type.fields['solids'].is_optional is True

    solids_type = env_type.fields['solids'].config_type

    assert solids_type.fields['int_config_solid'].is_optional is True

    solids_default_obj = construct_solid_dictionary(throwing_evaluate_config_value(solids_type, {}))

    assert solids_default_obj['int_config_solid'].config is None

    env_obj = EnvironmentConfig.from_dict(throwing_evaluate_config_value(env_type, {}))

    assert env_obj.solids['int_config_solid'].config is None


def test_optional_solid_with_required_scalar_config():
    def _assert_config_none(context, value):
        assert context.solid_config is value

    pipeline_def = PipelineDefinition(
        name='some_pipeline',
        solid_defs=[
            SolidDefinition(
                name='int_config_solid',
                config_field=Field(Int),
                input_defs=[],
                output_defs=[],
                compute_fn=lambda context, _inputs: _assert_config_none(context, 234),
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
        solid_defs=[
            SolidDefinition(
                name='int_config_solid',
                config_field=Field(Dict({'required_field': Field(String)})),
                input_defs=[],
                output_defs=[],
                compute_fn=lambda *_args: None,
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

    assert env_type.fields['execution'].is_optional
    assert env_type.fields['expectations'].is_optional

    env_obj = EnvironmentConfig.from_dict(
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
        solid_defs=[
            SolidDefinition(
                name='int_config_solid',
                config_field=Field(
                    Dict({'optional_field': Field(String, is_optional=True)}), is_optional=True
                ),
                input_defs=[],
                output_defs=[],
                compute_fn=lambda *_args: None,
            )
        ],
    )

    env_type = create_environment_type(pipeline_def)
    assert env_type.fields['solids'].is_optional
    assert env_type.fields['execution'].is_optional
    assert env_type.fields['expectations'].is_optional


def nested_field(config_type, *field_names):
    assert field_names

    field = config_type.fields[field_names[0]]

    for field_name in field_names[1:]:
        field = field.config_type.fields[field_name]

    return field


def test_required_resource_with_required_subfield():
    pipeline_def = PipelineDefinition(
        name='some_pipeline',
        solid_defs=[],
        mode_defs=[
            ModeDefinition(
                resource_defs={
                    'with_required': ResourceDefinition(
                        resource_fn=lambda: None,
                        config_field=Field(Dict({'required_field': Field(String)})),
                    )
                }
            )
        ],
    )

    env_type = create_environment_type(pipeline_def)
    assert env_type.fields['solids'].is_optional
    assert env_type.fields['execution'].is_optional
    assert env_type.fields['expectations'].is_optional
    assert env_type.fields['resources'].is_required
    assert nested_field(env_type, 'resources', 'with_required').is_required
    assert nested_field(env_type, 'resources', 'with_required', 'config').is_required
    assert nested_field(
        env_type, 'resources', 'with_required', 'config', 'required_field'
    ).is_required


def test_all_optional_field_on_single_resource():
    pipeline_def = PipelineDefinition(
        name='some_pipeline',
        solid_defs=[],
        mode_defs=[
            ModeDefinition(
                resource_defs={
                    'with_optional': ResourceDefinition(
                        resource_fn=lambda: None,
                        config_field=Field(
                            Dict({'optional_field': Field(String, is_optional=True)})
                        ),
                    )
                }
            )
        ],
    )

    env_type = create_environment_type(pipeline_def)
    assert env_type.fields['solids'].is_optional
    assert env_type.fields['execution'].is_optional
    assert env_type.fields['expectations'].is_optional
    assert env_type.fields['resources'].is_optional
    assert nested_field(env_type, 'resources', 'with_optional').is_optional
    assert nested_field(env_type, 'resources', 'with_optional', 'config').is_optional
    assert nested_field(
        env_type, 'resources', 'with_optional', 'config', 'optional_field'
    ).is_optional


def test_optional_and_required_context():
    pipeline_def = PipelineDefinition(
        name='some_pipeline',
        solid_defs=[],
        mode_defs=[
            ModeDefinition(
                name='mixed',
                resource_defs={
                    'optional_resource': ResourceDefinition(
                        lambda: None,
                        config_field=Field(
                            dagster_type=Dict(
                                fields={'optional_field': Field(String, is_optional=True)}
                            )
                        ),
                    ),
                    'required_resource': ResourceDefinition(
                        lambda: None,
                        config_field=Field(
                            dagster_type=Dict(fields={'required_field': Field(String)})
                        ),
                    ),
                },
            )
        ],
    )

    env_type = create_environment_type(pipeline_def)
    assert env_type.fields['solids'].is_optional

    assert env_type.fields['execution'].is_optional
    assert env_type.fields['expectations'].is_optional

    assert nested_field(env_type, 'resources').is_required
    assert nested_field(env_type, 'resources', 'optional_resource').is_optional
    assert nested_field(env_type, 'resources', 'optional_resource', 'config').is_optional
    assert nested_field(
        env_type, 'resources', 'optional_resource', 'config', 'optional_field'
    ).is_optional

    assert nested_field(env_type, 'resources', 'required_resource').is_required
    assert nested_field(env_type, 'resources', 'required_resource', 'config').is_required
    assert nested_field(
        env_type, 'resources', 'required_resource', 'config', 'required_field'
    ).is_required

    env_obj = EnvironmentConfig.from_dict(
        throwing_evaluate_config_value(
            env_type, {'resources': {'required_resource': {'config': {'required_field': 'foo'}}}}
        )
    )

    assert env_obj.resources == {
        'optional_resource': {'config': {}},
        'required_resource': {'config': {'required_field': 'foo'}},
    }


def test_required_inputs():
    @lambda_solid(input_defs=[InputDefinition('num', Int)], output_def=OutputDefinition(Int))
    def add_one(num):
        return num + 1

    pipeline_def = PipelineDefinition(
        name='required_int_input',
        solid_defs=[add_one],
        dependencies={
            SolidInvocation('add_one', 'first_add'): {},
            SolidInvocation('add_one', 'second_add'): {'num': DependencyDefinition('first_add')},
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
        input_defs=[InputDefinition('left', Int), InputDefinition('right', Int)],
        output_def=OutputDefinition(Int),
    )
    def add_numbers(left, right):
        return left + right

    @lambda_solid
    def return_three():
        return 3

    pipeline_def = PipelineDefinition(
        name='mixed_required_inputs',
        solid_defs=[add_numbers, return_three],
        dependencies={'add_numbers': {'right': DependencyDefinition('return_three')}},
    )

    env_type = create_environment_type(pipeline_def)
    solids_type = env_type.fields['solids'].config_type
    add_numbers_type = solids_type.fields['add_numbers'].config_type
    inputs_fields_dict = add_numbers_type.fields['inputs'].config_type.fields

    assert 'left' in inputs_fields_dict
    assert not 'right' in inputs_fields_dict


def test_files_default_config():
    pipeline_def = PipelineDefinition(name='pipeline', solid_defs=[])

    env_type = create_environment_type(pipeline_def)
    assert 'storage' in env_type.fields

    config_value = throwing_evaluate_config_value(env_type, {})

    assert 'storage' not in config_value


def test_storage_in_memory_config():
    pipeline_def = PipelineDefinition(name='pipeline', solid_defs=[])

    env_type = create_environment_type(pipeline_def)
    assert 'storage' in env_type.fields

    config_value = throwing_evaluate_config_value(env_type, {'storage': {'in_memory': {}}})

    assert config_value['storage'] == {'in_memory': {}}
