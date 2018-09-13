import pytest

from dagster import (
    DagsterInvalidDefinitionError,
    DependencyDefinition,
    PipelineDefinition,
    SolidDefinition,
    OutputDefinition,
    InputDefinition,
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
