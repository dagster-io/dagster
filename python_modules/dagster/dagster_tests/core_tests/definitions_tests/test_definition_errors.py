import pytest

from dagster import (
    ConfigType,
    DagsterInvalidDefinitionError,
    DependencyDefinition,
    Dict,
    Field,
    InputDefinition,
    Int,
    NamedDict,
    OutputDefinition,
    PermissiveDict,
    PipelineDefinition,
    ResourceDefinition,
    SolidDefinition,
    String,
    solid,
)

from dagster.core.definitions import create_environment_schema
from dagster.core.types import Selector, NamedSelector
from dagster.core.utility_solids import define_stub_solid


def solid_a_b_list():
    return [
        SolidDefinition(
            name='A',
            input_defs=[],
            output_defs=[OutputDefinition()],
            compute_fn=lambda _context, _inputs: None,
        ),
        SolidDefinition(
            name='B',
            input_defs=[InputDefinition('b_input')],
            output_defs=[],
            compute_fn=lambda _context, _inputs: None,
        ),
    ]


def test_create_pipeline_with_bad_solids_list():
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match='"solids" arg to pipeline "a_pipeline" is not a list. Got',
    ):
        PipelineDefinition(
            name='a_pipeline', solid_defs=define_stub_solid('stub', [{'a key': 'a value'}])
        )


def test_circular_dep():
    with pytest.raises(DagsterInvalidDefinitionError, match='Circular reference'):
        PipelineDefinition(
            solid_defs=solid_a_b_list(),
            dependencies={'A': {}, 'B': {'b_input': DependencyDefinition('B')}},
        )


def test_from_solid_not_there():
    with pytest.raises(
        DagsterInvalidDefinitionError, match='Solid NOTTHERE in dependency dictionary not found'
    ):
        PipelineDefinition(
            solid_defs=solid_a_b_list(),
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
            solid_defs=solid_a_b_list(),
            dependencies={'B': {'not_an_input': DependencyDefinition('A')}},
        )


def test_to_solid_not_there():
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match='Solid NOTTHERE in DependencyDefinition not found in solid list',
    ):
        PipelineDefinition(
            solid_defs=solid_a_b_list(),
            dependencies={'A': {}, 'B': {'b_input': DependencyDefinition('NOTTHERE')}},
        )


def test_to_solid_output_not_there():
    with pytest.raises(
        DagsterInvalidDefinitionError, match='Solid A does not have output NOTTHERE'
    ):
        PipelineDefinition(
            solid_defs=solid_a_b_list(),
            dependencies={'B': {'b_input': DependencyDefinition('A', output='NOTTHERE')}},
        )


def test_invalid_item_in_solid_list():
    with pytest.raises(
        DagsterInvalidDefinitionError, match="Invalid item in solid list: 'not_a_solid'"
    ):
        PipelineDefinition(solid_defs=['not_a_solid'])


def test_one_layer_off_dependencies():
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="Received a IDependencyDefinition one layer too high under key B",
    ):
        PipelineDefinition(
            solid_defs=solid_a_b_list(), dependencies={'B': DependencyDefinition('A')}
        )


def test_malformed_dependencies():
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match='Expected IDependencyDefinition for solid "B" input "b_input"',
    ):
        PipelineDefinition(
            solid_defs=solid_a_b_list(),
            dependencies={'B': {'b_input': {'b_input': DependencyDefinition('A')}}},
        )


def test_list_dependencies():
    with pytest.raises(
        DagsterInvalidDefinitionError, match='The expected type for "dependencies" is dict'
    ):
        PipelineDefinition(solid_defs=solid_a_b_list(), dependencies=[])


def test_double_type_name():
    @solid(config_field=Field(NamedDict('SomeTypeName', {'some_field': Field(String)})))
    def solid_one(_context):
        raise Exception('should not execute')

    @solid(config_field=Field(NamedDict('SomeTypeName', {'another_field': Field(String)})))
    def solid_two(_context):
        raise Exception('should not execute')

    with pytest.raises(DagsterInvalidDefinitionError) as exc_info:
        create_environment_schema(PipelineDefinition(solid_defs=[solid_one, solid_two]))

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
        create_environment_schema(PipelineDefinition(solid_defs=[solid_one, solid_two]))

    assert str(exc_info.value) == (
        'Type keys must be unique. You have constructed two different instances of types '
        'with the same key "KeyOne".'
    )


def test_pass_config_type_to_field_error_solid_definition():
    with pytest.raises(DagsterInvalidDefinitionError) as exc_info:

        @solid(config_field=Dict({'val': Field(Int)}))
        def a_solid(_context):
            pass

        assert a_solid  # fool lint

    assert str(exc_info.value) == (
        'You have passed a config type "{ val: Int }" in the parameter "config_field" '
        'of a SolidDefinition or @solid named "a_solid". You have '
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
        'ResourceDefinition or @resource. You have likely forgot to '
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
        'You have passed a config type "Int" in the parameter "fields" and it is '
        'in the "val" entry of that dict. It is from a Dict with fields '
        '[\'another_val\', \'val\']. You have likely '
        'forgot to wrap this type in a Field.'
    )


def test_invalid_named_dict_field():
    with pytest.raises(DagsterInvalidDefinitionError) as exc_info:
        NamedDict('some_named_dict', {'val': Int, 'another_val': Field(Int)})

    assert str(exc_info.value) == (
        'You have passed a config type "Int" in the parameter "fields" and it is '
        'in the "val" entry of that dict. It is from a NamedDict named '
        '"some_named_dict" with fields [\'another_val\', \'val\']. You '
        'have likely forgot to wrap this type in a Field.'
    )


def test_invalid_permissive_dict_field():

    with pytest.raises(DagsterInvalidDefinitionError) as exc_info:
        PermissiveDict({'val': Int, 'another_val': Field(Int)})

    assert str(exc_info.value) == (
        'You have passed a config type "Int" in the parameter "fields" and it is '
        'in the "val" entry of that dict. It is from a PermissiveDict with fields '
        '[\'another_val\', \'val\']. You have likely '
        'forgot to wrap this type in a Field.'
    )


def test_invalid_selector_field():
    with pytest.raises(DagsterInvalidDefinitionError) as exc_info:
        Selector({'val': Int})

    assert str(exc_info.value) == (
        'You have passed a config type "Int" in the parameter "fields" and it is '
        'in the "val" entry of that dict. It is from a Selector with fields '
        '[\'val\']. You have likely forgot to wrap this type in a Field.'
    )


def test_invalid_named_selector_field():
    with pytest.raises(DagsterInvalidDefinitionError) as exc_info:
        NamedSelector('some_selector', {'val': Int})

    assert str(exc_info.value) == (
        'You have passed a config type "Int" in the parameter "fields" and it is '
        'in the "val" entry of that dict. It is from a NamedSelector named '
        '"some_selector" with fields [\'val\']. You '
        'have likely forgot to wrap this type in a Field.'
    )
