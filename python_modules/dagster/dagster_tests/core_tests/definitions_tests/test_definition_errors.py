import pytest

import dagster.check as check

from dagster import (
    ConfigType,
    DagsterInvalidDefinitionError,
    DependencyDefinition,
    Dict,
    Field,
    InputDefinition,
    Int,
    NamedDict,
    # NamedSelector,
    OutputDefinition,
    # PermissiveDict,
    PipelineContextDefinition,
    PipelineDefinition,
    ResourceDefinition,
    # Selector,
    SolidDefinition,
    String,
    solid,
)

from dagster.core.utility_solids import define_stub_solid


def solid_a_b_list():
    return [
        SolidDefinition(
            name='A',
            inputs=[],
            outputs=[OutputDefinition()],
            transform_fn=lambda _context, _inputs: None,
        ),
        SolidDefinition(
            name='B',
            inputs=[InputDefinition('b_input')],
            outputs=[],
            transform_fn=lambda _context, _inputs: None,
        ),
    ]


def test_create_pipeline_with_bad_solids_list():
    stub_solid = define_stub_solid('stub', [{'a key': 'a value'}])
    with pytest.raises(check.ParameterCheckError, match='Param "solids" is not a list.'):
        PipelineDefinition(solids=stub_solid, dependencies={})


def test_circular_dep():
    with pytest.raises(DagsterInvalidDefinitionError, match='Circular reference'):
        PipelineDefinition(
            solids=solid_a_b_list(),
            dependencies={'A': {}, 'B': {'b_input': DependencyDefinition('B')}},
        )


def test_from_solid_not_there():
    with pytest.raises(
        DagsterInvalidDefinitionError, match='Solid NOTTHERE in dependency dictionary not found'
    ):
        PipelineDefinition(
            solids=solid_a_b_list(),
            dependencies={
                'A': {},
                'B': {'b_input': DependencyDefinition('A')},
                'NOTTHERE': {'b_input': DependencyDefinition('A')},
            },
        )


def test_from_non_existant_input():
    with pytest.raises(
        DagsterInvalidDefinitionError, match='Solid "B" does not have input "not_an_input"'
    ):
        PipelineDefinition(
            solids=solid_a_b_list(), dependencies={'B': {'not_an_input': DependencyDefinition('A')}}
        )


def test_to_solid_not_there():
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match='Solid NOTTHERE in DependencyDefinition not found in solid list',
    ):
        PipelineDefinition(
            solids=solid_a_b_list(),
            dependencies={'A': {}, 'B': {'b_input': DependencyDefinition('NOTTHERE')}},
        )


def test_to_solid_output_not_there():
    with pytest.raises(
        DagsterInvalidDefinitionError, match='Solid A does not have output NOTTHERE'
    ):
        PipelineDefinition(
            solids=solid_a_b_list(),
            dependencies={'B': {'b_input': DependencyDefinition('A', output='NOTTHERE')}},
        )


def test_invalid_item_in_solid_list():
    with pytest.raises(
        DagsterInvalidDefinitionError, match="Invalid item in solid list: 'not_a_solid'"
    ):
        PipelineDefinition(solids=['not_a_solid'])


def test_double_type_name():
    @solid(config_field=Field(NamedDict('SomeTypeName', {'some_field': Field(String)})))
    def solid_one(_context):
        raise Exception('should not execute')

    @solid(config_field=Field(NamedDict('SomeTypeName', {'another_field': Field(String)})))
    def solid_two(_context):
        raise Exception('should not execute')

    with pytest.raises(DagsterInvalidDefinitionError) as exc_info:
        PipelineDefinition(solids=[solid_one, solid_two])

    assert str(exc_info.value) == (
        'Type names must be unique. You have constructed two different instances of '
        'types with the same name "SomeTypeName".'
    )


def test_double_type_key():
    class KeyOneNameOneType(ConfigType):
        def __init__(self):
            super(KeyOneNameOneType, self).__init__(key='KeyOne', name='NameOne')

    class KeyOneNameTwoType(ConfigType):
        def __init__(self):
            super(KeyOneNameTwoType, self).__init__(key='KeyOne', name='NameTwo')

    @solid(config_field=Field(KeyOneNameOneType))
    def solid_one(_context):
        raise Exception('should not execute')

    @solid(config_field=Field(KeyOneNameTwoType))
    def solid_two(_context):
        raise Exception('should not execute')

    with pytest.raises(DagsterInvalidDefinitionError) as exc_info:
        PipelineDefinition(solids=[solid_one, solid_two])

    assert str(exc_info.value) == (
        'Type keys must be unique. You have constructed two different instances of types '
        'with the same key "KeyOne".'
    )


def test_pass_config_type_to_field_error_context_definition():
    with pytest.raises(DagsterInvalidDefinitionError) as exc_info:
        PipelineDefinition(
            name='pass_config_type_to_context_def_config_field_error_pipeline',
            solids=[],
            context_definitions={
                'some_context': PipelineContextDefinition(config_field=Dict({'val': Field(Int)}))
            },
        )

    assert str(exc_info.value) == (
        'You have passed a config type "{ val: Int }" in the parameter "config_field" of a '
        'PipelineContextDefinition that expects a Field. You have likely forgot to '
        'wrap this type in a Field.'
    )


def test_pass_unrelated_type_to_field_error_context_definition():
    with pytest.raises(DagsterInvalidDefinitionError) as exc_info:
        PipelineDefinition(
            name='pass_unrelated_type_to_context_def_config_field_error_pipeline',
            solids=[],
            context_definitions={'some_context': PipelineContextDefinition(config_field='wut')},
        )

    assert str(exc_info.value) == (
        'You have passed an object \'wut\' of incorrect type "str" in the parameter '
        '"config_field" of a PipelineContextDefinition where a Field was expected.'
    )


def test_pass_config_type_to_field_error_solid_definition():

    with pytest.raises(DagsterInvalidDefinitionError) as exc_info:

        @solid(config_field=Dict({'val': Field(Int)}))
        def a_solid(_context):
            pass

        assert a_solid  # fool lint

    assert str(exc_info.value) == (
        'You have passed a config type "{ val: Int }" in the parameter "config_field" '
        'of a SolidDefinition or @solid named "a_solid" that expects a Field. You have '
        'likely forgot to wrap this type in a Field.'
    )


def test_pass_unrelated_type_to_field_error_solid_definition():

    with pytest.raises(DagsterInvalidDefinitionError) as exc_info:

        @solid(config_field='nope')
        def a_solid(_context):
            pass

        assert a_solid  # fool lint

    assert str(exc_info.value) == (
        'You have passed an object \'nope\' of incorrect type "str" in the parameter '
        '"config_field" of a SolidDefinition or @solid named "a_solid" where a Field '
        'was expected.'
    )


def test_pass_config_type_to_field_error_resource_definition():
    with pytest.raises(DagsterInvalidDefinitionError) as exc_info:
        ResourceDefinition(resource_fn=lambda: None, config_field=Dict({'val': Field(Int)}))

    assert str(exc_info.value) == (
        'You have passed a config type "{ val: Int }" in the parameter "config_field" of a '
        'ResourceDefinition or @resource that expects a Field. You have likely forgot to '
        'wrap this type in a Field.'
    )


def test_pass_unrelated_type_to_field_error_resource_definition():
    with pytest.raises(DagsterInvalidDefinitionError) as exc_info:
        ResourceDefinition(resource_fn=lambda: None, config_field='wut')

    assert str(exc_info.value) == (
        'You have passed an object \'wut\' of incorrect type "str" in the parameter '
        '"config_field" of a ResourceDefinition or @resource where a Field was expected.'
    )


def test_pass_incorrect_thing_to_field():
    with pytest.raises(DagsterInvalidDefinitionError) as exc_info:
        Field('nope')

    assert str(exc_info.value) == (
        'Attempted to pass \'nope\' to a Field that expects a valid dagster type '
        'usable in config (e.g. Dict, NamedDict, Int, String et al).'
    )


def test_invalid_dict_field():
    with pytest.raises(DagsterInvalidDefinitionError) as exc_info:
        Dict({'val': Int, 'another_val': Field(Int)})

    assert str(exc_info.value) == (
        'You have passed a config type "Int" in the parameter "fields" It is '
        'in the "val" entry of the field dict of a Dict with field names '
        '[\'val\', \'another_val\'] that expects a Field. You have likely '
        'forgot to wrap this type in a Field.'
    )


# def test_invalid_named_dict_field():
#     NamedDict('some_dict', {'val': Int})

# def test_invalid_permissive_dict_field():
#     NamedDict('some_dict', {'val': Int})

# def test_invalid_selector_field():
#     NamedDict('some_dict', {'val': Int})

# def test_invalid_named_selector_field():
#     NamedDict('some_dict', {'val': Int})
