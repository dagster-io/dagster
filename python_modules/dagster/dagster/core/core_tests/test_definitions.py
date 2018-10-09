from dagster import (
    ConfigDefinition,
    DependencyDefinition,
    Field,
    PipelineContextDefinition,
    PipelineDefinition,
    types,
    InputDefinition,
    OutputDefinition,
    lambda_solid,
    solid,
)


def test_deps_equal():
    assert DependencyDefinition('foo') == DependencyDefinition('foo')
    assert DependencyDefinition('foo') != DependencyDefinition('bar')

    assert DependencyDefinition('foo', 'bar') == DependencyDefinition('foo', 'bar')
    assert DependencyDefinition('foo', 'bar') != DependencyDefinition('foo', 'quuz')


def test_pipeline_types():
    ContextOneConfigDict = types.ConfigDictionary(
        'ContextOneConfigDict',
        {'field_one': Field(types.String)},
    )

    SolidOneConfigDict = types.ConfigDictionary(
        'SolidOneConfigDict',
        {'another_field': Field(types.Int)},
    )

    @lambda_solid
    def produce_string():
        return 'foo'

    @solid(
        inputs=[InputDefinition('input_one', types.String)],
        outputs=[OutputDefinition(types.Any)],
        config_def=ConfigDefinition(SolidOneConfigDict),
    )
    def solid_one(_info, input_one):
        raise Exception('should not execute')

    pipeline_def = PipelineDefinition(
        solids=[produce_string, solid_one],
        dependencies={'solid_one': {
            'input_one': DependencyDefinition('produce_string'),
        }},
        context_definitions={
            'context_one':
            PipelineContextDefinition(
                context_fn=lambda: None,
                config_def=ConfigDefinition(ContextOneConfigDict),
            )
        }
    )

    present_types = [
        SolidOneConfigDict,
        ContextOneConfigDict,
        types.String,
        types.Any,
        types.Int,
    ]

    for present_type in present_types:
        name = present_type.name
        assert pipeline_def.has_type(name)
        assert pipeline_def.type_named(name).name == name

    not_present_types = [
        types.PythonObjectType('Duisjdfke', dict),
    ]

    for not_present_type in not_present_types:
        assert not pipeline_def.has_type(not_present_type.name)
