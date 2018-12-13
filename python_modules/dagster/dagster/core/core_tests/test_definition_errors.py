import pytest

import dagster.check as check

from dagster import (
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

from dagster.core.utility_solids import define_stub_solid

from .test_pipeline_execution import create_solid_with_deps


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
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=
        'Solid B is passed to list of pipeline solids, but is not used in pipeline. You must define its dependencies:'
    ):
        PipelineDefinition(solids=solid_a_b_list(), dependencies={})


def test_missing_inputs():
    bar_solid = define_stub_solid('bar', [{'baz': 'bip'}])
    foo_solid = create_solid_with_deps('foo', bar_solid)
    baz_solid = create_solid_with_deps('baz', foo_solid)
    with pytest.raises(
        DagsterInvalidDefinitionError, match='Dependency must be specified for solid foo input bar'
    ):
        PipelineDefinition(
            solids=[baz_solid, foo_solid],
            dependencies={'baz': {
                'foo': DependencyDefinition('foo')
            }},
        )


def test_create_pipeline_with_bad_solids_list():
    stub_solid = define_stub_solid('stub', [{'a key': 'a value'}])
    with pytest.raises(check.ParameterCheckError, match='Param "solids" is not a list.'):
        PipelineDefinition(
            solids=stub_solid,
            dependencies={},
        )


def test_circular_dep():
    with pytest.raises(DagsterInvalidDefinitionError, match='Circular reference'):
        PipelineDefinition(
            solids=solid_a_b_list(),
            dependencies={
                'A': {},
                'B': {
                    'b_input': DependencyDefinition('B'),
                },
            },
        )


def test_from_solid_not_there():
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match='Solid NOTTHERE in dependency dictionary not found',
    ):
        PipelineDefinition(
            solids=solid_a_b_list(),
            dependencies={
                'A': {},
                'B': {
                    'b_input': DependencyDefinition('A'),
                },
                'NOTTHERE': {
                    'b_input': DependencyDefinition('A'),
                },
            },
        )


def test_from_non_existant_input():
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match='Solid B does not have input not_an_input',
    ):
        PipelineDefinition(
            solids=solid_a_b_list(),
            dependencies={
                'B': {
                    'not_an_input': DependencyDefinition('A'),
                },
            },
        )


def test_to_solid_not_there():
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match='Solid NOTTHERE in DependencyDefinition not found in solid list',
    ):
        PipelineDefinition(
            solids=solid_a_b_list(),
            dependencies={
                'A': {},
                'B': {
                    'b_input': DependencyDefinition('NOTTHERE'),
                },
            },
        )


def test_to_solid_output_not_there():
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match='Solid A does not have output NOTTHERE',
    ):
        PipelineDefinition(
            solids=solid_a_b_list(),
            dependencies={
                'B': {
                    'b_input': DependencyDefinition('A', output='NOTTHERE'),
                },
            },
        )


def test_invalid_item_in_solid_list():
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="Invalid item in solid list: 'not_a_solid'",
    ):
        PipelineDefinition(solids=['not_a_solid'])


def test_double_type():
    @solid(
        config_field=Field(
            types.DagsterCompositeType(
                'SomeTypeName',
                {'some_field': Field(types.String)},
            ),
        )
    )
    def solid_one(_info):
        raise Exception('should not execute')

    @solid(
        config_field=Field(
            types.DagsterCompositeType(
                'SomeTypeName',
                {'some_field': Field(types.String)},
            ),
        )
    )
    def solid_two(_info):
        raise Exception('should not execute')

    with pytest.raises(DagsterInvalidDefinitionError, match='Type names must be unique.'):
        PipelineDefinition(solids=[solid_one, solid_two])
