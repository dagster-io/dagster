import pytest

from dagster import (
    ConfigDefinition,
    DagsterInvalidDefinitionError,
    Field,
    DependencyDefinition,
    PipelineDefinition,
    SolidDefinition,
    OutputDefinition,
    InputDefinition,
    solid,
    types,
)


def solid_a_b_list():
    return [
        SolidDefinition(
            name='A',
            inputs=[],
            outputs=[OutputDefinition()],
            transform_fn=lambda _info, _inputs: None,
        ),
        SolidDefinition(
            name='B',
            inputs=[InputDefinition('b_input')],
            outputs=[],
            transform_fn=lambda _info, _inputs: None,
        )
    ]


def test_no_dep_specified():
    with pytest.raises(DagsterInvalidDefinitionError, message='Dependency must be specified'):
        PipelineDefinition(solids=solid_a_b_list(), dependencies={})


def test_circular_dep():
    with pytest.raises(DagsterInvalidDefinitionError, message='Circular reference'):
        PipelineDefinition(
            solids=solid_a_b_list(),
            dependencies={'B': {
                'b_input': DependencyDefinition('B')
            }},
        )


def test_from_solid_not_there():
    with pytest.raises(
        DagsterInvalidDefinitionError,
        message='Solid NOTTHERE in dependency dictionary not found',
    ):
        PipelineDefinition(
            solids=solid_a_b_list(),
            dependencies={'NOTTHERE': {
                'b_input': DependencyDefinition('A')
            }},
        )


def test_from_non_existant_input():
    with pytest.raises(
        DagsterInvalidDefinitionError,
        message='Solid B does not have input not_an_input',
    ):
        PipelineDefinition(
            solids=solid_a_b_list(),
            dependencies={'B': {
                'not_an_input': DependencyDefinition('A')
            }},
        )


def test_to_solid_not_there():
    with pytest.raises(
        DagsterInvalidDefinitionError,
        message='Solid NOTTHERE in DependencyDefinition not found in solid list',
    ):
        PipelineDefinition(
            solids=solid_a_b_list(),
            dependencies={'B': {
                'b_input': DependencyDefinition('NOTTHERE')
            }},
        )


def test_to_solid_output_not_there():
    with pytest.raises(
        DagsterInvalidDefinitionError,
        message='Solid A does not have output NOTTHERE',
    ):
        PipelineDefinition(
            solids=solid_a_b_list(),
            dependencies={'B': {
                'b_input': DependencyDefinition('A', output='NOTTHERE')
            }},
        )


def test_invalid_item_in_solid_list():
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="Invalid item in solid list: 'not_a_solid'",
    ):
        PipelineDefinition(solids=['not_a_solid'])


def test_double_type():
    @solid(
        config_def=ConfigDefinition(
            types.ConfigDictionary(
                'SomeTypeName',
                {'some_field': Field(types.String)},
            ),
        )
    )
    def solid_one(_info):
        raise Exception('should not execute')

    @solid(
        config_def=ConfigDefinition(
            types.ConfigDictionary(
                'SomeTypeName',
                {'some_field': Field(types.String)},
            ),
        )
    )
    def solid_two(_info):
        raise Exception('should not execute')

    with pytest.raises(DagsterInvalidDefinitionError, match='Type names must be unique.'):
        PipelineDefinition(solids=[solid_one, solid_two])
