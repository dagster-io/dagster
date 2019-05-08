import pytest

from dagster import (
    DependencyDefinition,
    Dict,
    Field,
    InputDefinition,
    OutputDefinition,
    PipelineContextDefinition,
    PipelineDefinition,
    SolidInstance,
    String,
    lambda_solid,
    solid,
    types,
)
from dagster.core.definitions import Solid, Materialization, create_environment_schema
from dagster.core.definitions.dependency import SolidOutputHandle
from dagster.core.errors import DagsterInvalidDefinitionError


def test_deps_equal():
    assert DependencyDefinition('foo') == DependencyDefinition('foo')
    assert DependencyDefinition('foo') != DependencyDefinition('bar')

    assert DependencyDefinition('foo', 'bar') == DependencyDefinition('foo', 'bar')
    assert DependencyDefinition('foo', 'bar') != DependencyDefinition('foo', 'quuz')


def test_solid_def():
    @lambda_solid
    def produce_string():
        return 'foo'

    @solid(
        inputs=[InputDefinition('input_one', types.String)],
        outputs=[OutputDefinition(types.Any)],
        config_field=Field(Dict({'another_field': Field(types.Int)})),
    )
    def solid_one(_context, input_one):
        raise Exception('should not execute')

    pipeline_def = PipelineDefinition(
        solids=[produce_string, solid_one],
        dependencies={'solid_one': {'input_one': DependencyDefinition('produce_string')}},
    )

    assert len(pipeline_def.solids[0].output_handles()) == 1

    assert isinstance(pipeline_def.solid_named('solid_one'), Solid)

    solid_one_solid = pipeline_def.solid_named('solid_one')

    assert solid_one_solid.has_input('input_one')

    assert isinstance(solid_one_solid.input_def_named('input_one'), InputDefinition)

    assert len(solid_one_solid.input_dict) == 1
    assert len(solid_one_solid.output_dict) == 1

    assert str(solid_one_solid.input_handle('input_one')) == (
        'SolidInputHandle(definition_name="\'solid_one\'", input_name="\'input_one\'", '
        'solid_name="\'solid_one\'")'
    )

    assert repr(solid_one_solid.input_handle('input_one')) == (
        'SolidInputHandle(definition_name="\'solid_one\'", input_name="\'input_one\'", '
        'solid_name="\'solid_one\'")'
    )

    assert str(solid_one_solid.output_handle('result')) == (
        'SolidOutputHandle(definition_name="\'solid_one\'", output_name="\'result\'", '
        'solid_name="\'solid_one\'")'
    )

    assert repr(solid_one_solid.output_handle('result')) == (
        'SolidOutputHandle(definition_name="\'solid_one\'", output_name="\'result\'", '
        'solid_name="\'solid_one\'")'
    )

    assert solid_one_solid.output_handle('result') == SolidOutputHandle(
        solid_one_solid, solid_one_solid.output_dict['result']
    )

    assert len(pipeline_def.dependency_structure.deps_of_solid_with_input('solid_one')) == 1

    assert len(pipeline_def.dependency_structure.depended_by_of_solid('produce_string')) == 1

    assert len(pipeline_def.dependency_structure.input_handles()) == 1

    assert len(pipeline_def.dependency_structure.items()) == 1


def test_pipeline_types():
    @lambda_solid
    def produce_string():
        return 'foo'

    @solid(
        inputs=[InputDefinition('input_one', types.String)],
        outputs=[OutputDefinition(types.Any)],
        config_field=Field(Dict({'another_field': Field(types.Int)})),
    )
    def solid_one(_context, input_one):
        raise Exception('should not execute')

    pipeline_def = PipelineDefinition(
        solids=[produce_string, solid_one],
        dependencies={'solid_one': {'input_one': DependencyDefinition('produce_string')}},
        context_definitions={
            'context_one': PipelineContextDefinition(
                context_fn=lambda: None, config_field=Field(Dict({'field_one': Field(String)}))
            )
        },
    )

    environment_schema = create_environment_schema(pipeline_def)

    assert environment_schema.has_config_type('String')
    assert environment_schema.has_config_type('Int')
    assert not environment_schema.has_config_type('SomeName')


def test_mapper_errors():
    @lambda_solid
    def solid_a():
        print('a: 1')
        return 1

    with pytest.raises(DagsterInvalidDefinitionError) as excinfo_1:
        PipelineDefinition(
            solids=[solid_a], dependencies={'solid_b': {'arg_a': DependencyDefinition('solid_a')}}
        )
    assert str(excinfo_1.value) == 'Solid solid_b in dependency dictionary not found in solid list'

    with pytest.raises(DagsterInvalidDefinitionError) as excinfo_2:
        PipelineDefinition(
            solids=[solid_a],
            dependencies={
                SolidInstance('solid_b', alias='solid_c'): {
                    'arg_a': DependencyDefinition('solid_a')
                }
            },
        )
    assert (
        str(excinfo_2.value)
        == 'Solid solid_b (aliased by solid_c in dependency dictionary) not found in solid list'
    )


def test_materialization():
    assert isinstance(Materialization('foo', 'foo.txt'), Materialization)
