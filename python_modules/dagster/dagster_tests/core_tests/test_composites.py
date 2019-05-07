from dagster import (
    CompositeSolidDefinition,
    DependencyDefinition,
    PipelineDefinition,
    SolidInstance,
    execute_pipeline,
)
from dagster.core.utility_solids import (
    create_root_solid,
    create_solid_with_deps,
    define_stub_solid,
    input_set,
)


def test_composite_basic_execution():
    a_source = define_stub_solid('A_source', [input_set('A_input')])
    node_a = create_root_solid('A')
    node_b = create_solid_with_deps('B', node_a)
    node_c = create_solid_with_deps('C', node_a)
    node_d = create_solid_with_deps('D', node_b, node_c)

    diamond_composite = CompositeSolidDefinition(
        name='diamond_composite',
        solids=[a_source, node_a, node_b, node_c, node_d],
        dependencies={
            'A': {'A_input': DependencyDefinition('A_source')},
            'B': {'A': DependencyDefinition('A')},
            'C': {'A': DependencyDefinition('A')},
            'D': {'B': DependencyDefinition('B'), 'C': DependencyDefinition('C')},
        },
    )

    result = execute_pipeline(PipelineDefinition(solids=[diamond_composite]))
    assert result.success

    result = execute_pipeline(
        PipelineDefinition(
            solids=[diamond_composite],
            dependencies={
                SolidInstance('diamond_composite', alias='D1'): {},
                SolidInstance('diamond_composite', alias='D2'): {},
            },
        )
    )
    assert result.success

    wrapped_composite = CompositeSolidDefinition(
        name='wrapped_composite', solids=[diamond_composite]
    )
    result = execute_pipeline(PipelineDefinition(solids=[diamond_composite, wrapped_composite]))
    assert result.success

    empty_composite = CompositeSolidDefinition(name='empty', solids=[])
    result = execute_pipeline(PipelineDefinition(solids=[empty_composite]))
    assert result.success
