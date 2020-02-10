import os

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
    execute_pipeline,
    execute_solid,
    lambda_solid,
    pipeline,
    solid,
    usable_as_dagster_type,
)
from dagster.core.test_utils import nesting_composite_pipeline
from dagster.core.utility_solids import (
    create_root_solid,
    create_solid_with_deps,
    define_stub_solid,
    input_set,
)
from dagster.utils.test import get_temp_dir


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

    res = execute_solid(diamond_composite)
    assert res.success

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

    nested_pipeline = nesting_composite_pipeline(6, 2)

    result = execute_pipeline(nested_pipeline)
    assert result.success


def test_composite_config():
    called = {}

    @solid(config=Field(String))
    def configured(context):
        called['configured'] = True
        assert context.solid_config == 'yes'

    @composite_solid
    def inner():
        configured()

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
        assert one == 1

    @composite_solid
    def inner():
        node_a()

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
        assert one == 1

    @composite_solid
    def inner(inner_one):
        node_a(inner_one)

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
    @usable_as_dagster_type
    class Foo(object):
        pass

    @solid(output_defs=[OutputDefinition(Foo)])
    def inner_solid(_context):
        return Foo()

    @composite_solid
    def middle_solid():
        inner_solid()

    @composite_solid
    def outer_solid():
        middle_solid()

    @pipeline
    def layered_types():
        outer_solid()

    assert layered_types.has_runtime_type('Foo')


def test_deep_mapping():
    @lambda_solid(output_def=OutputDefinition(String))
    def echo(blah):
        return blah

    @lambda_solid(output_def=OutputDefinition(String))
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


def test_mapping_parrallel_composite():
    @lambda_solid(output_def=OutputDefinition(int))
    def one():
        return 1

    @lambda_solid(output_def=OutputDefinition(int))
    def two():
        return 2

    @lambda_solid(
        input_defs=[
            InputDefinition(dagster_type=int, name='a'),
            InputDefinition(dagster_type=int, name='b'),
        ],
        output_def=OutputDefinition(int),
    )
    def adder(a, b):
        return a + b

    @composite_solid(
        output_defs=[
            OutputDefinition(dagster_type=int, name='two'),
            OutputDefinition(dagster_type=int, name='four'),
        ]
    )
    def composite_adder():
        result_one = one()
        result_two = two()

        calc_two = adder.alias('calc_two')
        calc_four = adder.alias('calc_four')

        calc_result_two = calc_two(result_one, result_one)
        calc_result_four = calc_four(result_two, result_two)

        return {'two': calc_result_two, 'four': calc_result_four}

    @lambda_solid
    def assert_four(val):
        assert val == 4

    @lambda_solid
    def assert_two(val):
        assert val == 2

    @pipeline
    def recreate_issue_pipeline():
        result = composite_adder()

        assert_two(result.two)  # pylint: disable=no-member
        assert_four(result.four)  # pylint: disable=no-member

    assert execute_pipeline(recreate_issue_pipeline).success


def test_composite_config_driven_materialization():
    @lambda_solid
    def one():
        return 1

    @composite_solid
    def wrap_one():
        return one()

    @pipeline
    def composite_config_driven_materialization_pipeline():
        wrap_one()

    with get_temp_dir() as write_directory:
        write_location = os.path.join(write_directory, 'wrap_one.json')
        execute_pipeline(
            composite_config_driven_materialization_pipeline,
            environment_dict={
                'solids': {
                    'wrap_one': {'outputs': [{'result': {'json': {'path': write_location}}}]}
                }
            },
        )

        assert os.path.exists(write_location)


def test_mapping_errors():
    @lambda_solid
    def echo(foo):
        return foo

    with pytest.raises(
        DagsterInvalidDefinitionError, match="references solid 'inner' which it does not contain"
    ):
        CompositeSolidDefinition(
            name='bad',
            solid_defs=[echo],
            input_mappings=[InputDefinition('mismatch').mapping_to('inner', 'foo')],
        )

    with pytest.raises(DagsterInvalidDefinitionError, match="no input named 'bar'"):
        CompositeSolidDefinition(
            name='bad',
            solid_defs=[echo],
            input_mappings=[InputDefinition('mismatch').mapping_to('echo', 'bar')],
        )

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="InputMapping source and destination must have the same type",
    ):
        CompositeSolidDefinition(
            name='bad',
            solid_defs=[echo],
            input_mappings=[InputDefinition('mismatch', str).mapping_to('echo', 'foo')],
        )

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="mappings with same definition name but different definitions",
    ):
        CompositeSolidDefinition(
            name='bad',
            solid_defs=[echo],
            input_mappings=[
                InputDefinition('mismatch').mapping_to('echo', 'foo'),
                InputDefinition('mismatch').mapping_to('echo_2', 'foo'),
            ],
        )

    with pytest.raises(
        DagsterInvalidDefinitionError, match="references solid 'inner' which it does not contain"
    ):
        CompositeSolidDefinition(
            name='bad',
            solid_defs=[echo],
            output_mappings=[OutputDefinition().mapping_from('inner', 'result')],
        )

    with pytest.raises(DagsterInvalidDefinitionError, match="no output named 'return'"):
        CompositeSolidDefinition(
            name='bad',
            solid_defs=[echo],
            output_mappings=[OutputDefinition().mapping_from('echo', 'return')],
        )

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="OutputMapping source and destination must have the same type",
    ):
        CompositeSolidDefinition(
            name='bad',
            solid_defs=[echo],
            output_mappings=[OutputDefinition(str).mapping_from('echo', 'result')],
        )
