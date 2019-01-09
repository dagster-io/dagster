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
from dagster.core.errors import DagsterInvalidDefinitionError


def test_deps_equal():
    assert DependencyDefinition('foo') == DependencyDefinition('foo')
    assert DependencyDefinition('foo') != DependencyDefinition('bar')

    assert DependencyDefinition('foo', 'bar') == DependencyDefinition('foo', 'bar')
    assert DependencyDefinition('foo', 'bar') != DependencyDefinition('foo', 'quuz')


def test_pipeline_types():
    @lambda_solid
    def produce_string():
        return 'foo'

    @solid(
        inputs=[InputDefinition('input_one', types.String)],
        outputs=[OutputDefinition(types.Any)],
        config_field=Field(Dict({'another_field': Field(types.Int)})),
    )
    def solid_one(_info, input_one):
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

    assert pipeline_def.has_config_type('String')
    assert pipeline_def.has_config_type('Int')
    assert not pipeline_def.has_config_type('SomeName')


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
