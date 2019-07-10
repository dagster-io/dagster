import pytest

from dagster import (
    CompositeSolidDefinition,
    DagsterInvalidDefinitionError,
    DependencyDefinition,
    Field,
    InputDefinition,
    OutputDefinition,
    PipelineDefinition,
    String,
    composite_solid,
    dagster_type,
    execute_pipeline,
    lambda_solid,
    pipeline,
    solid,
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

    @composite_solid
    def diamond_composite():
        a = node_a(a_source())
        node_d(B=node_b(a), C=node_c(a))

    @pipeline
    def test_pipeline_single():
        diamond_composite()

    result = execute_pipeline(test_pipeline_single)
    assert result.success

    @pipeline
    def test_pipeline_double():
        diamond_composite.alias('D1')()
        diamond_composite.alias('D2')()

    result = execute_pipeline(test_pipeline_double)
    assert result.success

    @composite_solid
    def wrapped_composite():
        diamond_composite()

    @pipeline
    def test_pipeline_mixed():
        diamond_composite()
        wrapped_composite()

    result = execute_pipeline(test_pipeline_mixed)
    assert result.success

    @composite_solid
    def empty():
        pass

    @pipeline
    def test_pipeline_empty():
        empty()

    result = execute_pipeline(test_pipeline_empty)
    assert result.success


def test_composite_config():
    called = {}

    @solid(config_field=Field(String))
    def configured(context):
        called['configured'] = True
        assert context.solid_config is 'yes'

    @composite_solid
    def inner():
        configured()  # pylint: disable=no-value-for-parameter

    @composite_solid
    def outer():
        inner()

    @pipeline
    def composites_pipeline():
        outer()

    result = execute_pipeline(
        composites_pipeline,
        {'solids': {'outer': {'solids': {'inner': {'solids': {'configured': {'config': 'yes'}}}}}}},
    )
    assert result.success
    assert called['configured']


def test_composite_config_input():
    called = {}

    @solid(input_defs=[InputDefinition('one')])
    def node_a(_context, one):
        called['node_a'] = True
        assert one is 1

    @composite_solid
    def inner():
        node_a()  # pylint: disable=no-value-for-parameter

    @composite_solid
    def outer():
        inner()

    @pipeline
    def composites_pipeline():
        outer()

    result = execute_pipeline(
        composites_pipeline,
        {
            'solids': {
                'outer': {
                    'solids': {'inner': {'solids': {'node_a': {'inputs': {'one': {'value': 1}}}}}}
                }
            }
        },
    )
    assert result.success
    assert called['node_a']


def test_mapped_composite_config_input():
    called = {}

    @solid(input_defs=[InputDefinition('one')])
    def node_a(_context, one):
        called['node_a'] = True
        assert one is 1

    @composite_solid
    def inner(inner_one):
        node_a(inner_one)  # pylint: disable=no-value-for-parameter

    outer = CompositeSolidDefinition(
        name='outer',
        solid_defs=[inner],
        input_mappings=[InputDefinition('outer_one').mapping_to('inner', 'inner_one')],
    )
    pipe = PipelineDefinition(name='composites_pipeline', solid_defs=[outer])

    result = execute_pipeline(pipe, {'solids': {'outer': {'inputs': {'outer_one': {'value': 1}}}}})
    assert result.success
    assert called['node_a']


def test_composite_io_mapping():
    a_source = define_stub_solid('A_source', [input_set('A_input')])
    node_a = create_root_solid('A')

    node_b = create_solid_with_deps('B', node_a)
    node_c = create_solid_with_deps('C', node_b)

    comp_a_inner = CompositeSolidDefinition(
        name='comp_a_inner',
        solid_defs=[a_source, node_a],
        dependencies={'A': {'A_input': DependencyDefinition('A_source')}},
        output_mappings=[OutputDefinition().mapping_from('A')],
    )

    comp_a_outer = CompositeSolidDefinition(
        name='comp_a_outer',
        solid_defs=[comp_a_inner],
        output_mappings=[OutputDefinition().mapping_from('comp_a_inner')],
    )

    comp_bc_inner = CompositeSolidDefinition(
        name='comp_bc_inner',
        solid_defs=[node_b, node_c],
        dependencies={'C': {'B': DependencyDefinition('B')}},
        input_mappings=[
            InputDefinition(name='inner_B_in').mapping_to(solid_name='B', input_name='A')
        ],
    )

    comp_bc_outer = CompositeSolidDefinition(
        name='comp_bc_outer',
        solid_defs=[comp_bc_inner],
        dependencies={},
        input_mappings=[
            InputDefinition(name='outer_B_in').mapping_to(
                solid_name='comp_bc_inner', input_name='inner_B_in'
            )
        ],
    )

    @pipeline
    def wrapped_io():
        comp_bc_outer(comp_a_outer())

    result = execute_pipeline(wrapped_io)
    assert result.success


def test_io_error_is_decent():
    with pytest.raises(DagsterInvalidDefinitionError, match='mapping_to'):
        CompositeSolidDefinition(
            name='comp_a_outer', solid_defs=[], input_mappings=[InputDefinition('should_be_mapped')]
        )

    with pytest.raises(DagsterInvalidDefinitionError, match='mapping_from'):
        CompositeSolidDefinition(
            name='comp_a_outer', solid_defs=[], output_mappings=[OutputDefinition()]
        )


def test_types_descent():
    @dagster_type
    class Foo(object):
        pass

    @solid(output_defs=[OutputDefinition(Foo)])
    def inner_solid(_context):
        return Foo()

    @composite_solid
    def middle_solid():
        inner_solid()  # pylint: disable=no-value-for-parameter

    @composite_solid
    def outer_solid():
        middle_solid()

    @pipeline
    def layered_types():
        outer_solid()

    assert layered_types.has_runtime_type('Foo')


def test_deep_mapping():
    @lambda_solid
    def echo(blah):
        return blah

    @lambda_solid
    def emit_foo():
        return 'foo'

    @composite_solid(output_defs=[OutputDefinition(String, 'z')])
    def az(a):
        return echo(a)

    @composite_solid(output_defs=[OutputDefinition(String, 'y')])
    def by(b):
        return az(b)

    @composite_solid(output_defs=[OutputDefinition(String, 'x')])
    def cx(c):
        return by(c)

    @pipeline
    def nested():
        echo(cx(emit_foo()))

    result = execute_pipeline(nested)
    assert result.result_for_solid('echo').output_value() == 'foo'
