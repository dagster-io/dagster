import pytest

from dagster import (
    DependencyDefinition,
    Field,
    InputDefinition,
    Int,
    OutputDefinition,
    PipelineDefinition,
    RepositoryDefinition,
    Result,
    composite_solid,
    execute_pipeline,
    lambda_solid,
    pipeline,
    solid,
)

from dagster.core.errors import DagsterInvalidDefinitionError


def builder(graph):
    return graph.add_one(graph.return_one())


@lambda_solid
def return_one():
    return 1


@lambda_solid
def return_two():
    return 2


@lambda_solid(inputs=[InputDefinition('num')])
def add_one(num):
    return num + 1


@lambda_solid(inputs=[InputDefinition('num')])
def pipe(num):
    return num


@solid(inputs=[InputDefinition('int_1', Int), InputDefinition('int_2', Int)])
def adder(_context, int_1, int_2):
    return int_1 + int_2


@solid(outputs=[OutputDefinition(Int, 'one'), OutputDefinition(Int, 'two')])
def return_mult(_context):
    yield Result(1, 'one')
    yield Result(2, 'two')


def test_basic():
    @composite_solid
    def test(_context):
        one = return_one()
        add_one(num=one)

    assert (
        execute_pipeline(PipelineDefinition(solid_defs=[test]))
        .result_for_handle('test.add_one')
        .result_value()
        == 2
    )


def test_args():
    @composite_solid
    def _test_1(_context):
        one = return_one()
        add_one(one)

    @composite_solid
    def _test_2(_context):
        # pylint: disable=no-value-for-parameter
        adder(return_one(), return_two())

    @composite_solid
    def _test_3(_context):
        # pylint: disable=no-value-for-parameter
        adder(int_1=return_one(), int_2=return_two())

    @composite_solid
    def _test_4(context):
        adder(context, return_one(), return_two())

    @composite_solid
    def _test_5(context):
        adder(context, return_one(), int_2=return_two())

    @composite_solid
    def _test_6(context):
        # pylint: disable=no-value-for-parameter
        adder(context, return_one())

    @composite_solid
    def _test_7(context):
        # pylint: disable=no-value-for-parameter
        adder(context, int_2=return_two())


def test_arg_fails():

    with pytest.raises(DagsterInvalidDefinitionError):

        @composite_solid
        def _fail_1(context):
            adder(context, context, return_one())

    with pytest.raises(DagsterInvalidDefinitionError):

        @composite_solid
        def _fail_2(context):
            adder(context, return_one(), 1)

    with pytest.raises(DagsterInvalidDefinitionError):

        @composite_solid
        def _fail_3(context):
            # pylint: disable=too-many-function-args
            adder(context, return_one(), return_two(), return_one.alias('three')())


def test_mult_out_fail():

    with pytest.raises(DagsterInvalidDefinitionError):

        @composite_solid
        def _test(context):
            ret = return_mult(context)
            add_one(ret)


def test_dupes_fail():
    with pytest.raises(DagsterInvalidDefinitionError):

        @composite_solid
        def _test(context):
            one, two = return_mult(context)
            add_one(num=one)
            add_one(num=two)


def test_multiple():
    @composite_solid
    def test(context):
        one, two = return_mult(context)
        add_one(num=one)
        add_one.alias('add_one_2')(num=two)

    results = execute_pipeline(PipelineDefinition(solid_defs=[test]))
    assert results.result_for_handle('test.add_one').result_value() == 2
    assert results.result_for_handle('test.add_one_2').result_value() == 3


def test_two_inputs_with_dsl():
    @lambda_solid(inputs=[InputDefinition('num_one'), InputDefinition('num_two')])
    def add(num_one, num_two):
        return num_one + num_two

    @lambda_solid
    def return_three():
        return 3

    @composite_solid
    def test(_context):
        add(num_one=return_two(), num_two=return_three())

    assert (
        execute_pipeline(PipelineDefinition(solid_defs=[test]))
        .result_for_handle('test.add')
        .result_value()
        == 5
    )


def test_basic_aliasing_with_dsl():
    @composite_solid
    def test(_context):
        add_one.alias('renamed')(num=return_one())

    assert (
        execute_pipeline(PipelineDefinition(solid_defs=[test]))
        .result_for_handle('test.renamed')
        .result_value()
        == 2
    )


def test_diamond_graph():
    @solid(outputs=[OutputDefinition(name='value_one'), OutputDefinition(name='value_two')])
    def emit_values(_context):
        yield Result(1, 'value_one')
        yield Result(2, 'value_two')

    @lambda_solid(inputs=[InputDefinition('num_one'), InputDefinition('num_two')])
    def add(num_one, num_two):
        return num_one + num_two

    @composite_solid
    def diamond(context):
        value_one, value_two = emit_values(context)
        add(num_one=add_one(num=value_one), num_two=add_one.alias('renamed')(num=value_two))

    result = execute_pipeline(PipelineDefinition(solid_defs=[diamond]))

    assert result.result_for_handle('diamond.add').result_value() == 5


def test_mapping():
    @lambda_solid(inputs=[InputDefinition('num_in', Int)], output=OutputDefinition(Int, 'num_out'))
    def double(num_in):
        return num_in * 2

    @composite_solid(
        inputs=[InputDefinition('num_in', Int)], outputs=[OutputDefinition(Int, 'num_out')]
    )
    def composed_inout(_context, num_in):
        return double(num_in=num_in)

    # have to use "pipe" solid since "result_for_solid" doesnt work with composite mappings
    assert (
        execute_pipeline(
            PipelineDefinition(
                solid_defs=[return_one, composed_inout, pipe],
                dependencies={
                    'composed_inout': {'num_in': DependencyDefinition('return_one')},
                    'pipe': {'num': DependencyDefinition('composed_inout', 'num_out')},
                },
            )
        )
        .result_for_solid('pipe')
        .result_value()
        == 2
    )


def output_map_mult():
    @composite_solid(outputs=[OutputDefinition(Int, 'one'), OutputDefinition(Int, 'two')])
    def wrap_mult(context):
        return return_mult(context)

    result = execute_pipeline(PipelineDefinition(solid_defs=[wrap_mult])).result_for_solid(
        'wrap_mult'
    )
    assert result.result_value('one') == 1
    assert result.result_value('two') == 2


def test_output_map_fail():
    with pytest.raises(DagsterInvalidDefinitionError):

        @composite_solid(outputs=[OutputDefinition(Int, 'one'), OutputDefinition(Int, 'two')])
        def _bad(_context):
            return return_one()

    with pytest.raises(DagsterInvalidDefinitionError):

        @composite_solid(outputs=[OutputDefinition(Int, 'one'), OutputDefinition(Int, 'two')])
        def _bad(_context):
            return {'one': 1}

    with pytest.raises(DagsterInvalidDefinitionError):

        @composite_solid(outputs=[OutputDefinition(Int, 'three'), OutputDefinition(Int, 'four')])
        def _bad(context):
            return return_mult(context)


def test_deep_graph():
    @solid(config_field=Field(Int))
    def download_num(context):
        return context.solid_config

    @lambda_solid(inputs=[InputDefinition('num')])
    def unzip_num(num):
        return num

    @lambda_solid(inputs=[InputDefinition('num')])
    def ingest_num(num):
        return num

    @lambda_solid(inputs=[InputDefinition('num')])
    def subsample_num(num):
        return num

    @lambda_solid(inputs=[InputDefinition('num')])
    def canonicalize_num(num):
        return num

    @lambda_solid(inputs=[InputDefinition('num')])
    def load_num(num):
        return num + 3

    @composite_solid(outputs=[OutputDefinition(Int)])
    def test(context):
        return load_num(
            num=canonicalize_num(
                num=subsample_num(num=ingest_num(num=unzip_num(num=download_num(context))))
            )
        )

    result = execute_pipeline(
        PipelineDefinition(solid_defs=[test]),
        {'solids': {'test': {'solids': {'download_num': {'config': 123}}}}},
    )
    assert result.result_for_handle('test.canonicalize_num').result_value() == 123
    assert result.result_for_handle('test.load_num').result_value() == 126


def test_recursion():
    @composite_solid
    def outer(context):
        @composite_solid(outputs=[OutputDefinition()])
        def inner(_context):
            return add_one(return_one())

        add_one(inner(context))

    assert execute_pipeline(PipelineDefinition(solid_defs=[outer])).success


class Garbage(Exception):
    pass


def test_recursion_with_exceptions():
    called = {}

    @pipeline
    def recurse(context):
        @composite_solid
        def outer(context):
            try:

                @composite_solid
                def throws(_context):
                    called['throws'] = True
                    raise Garbage()

                throws(context)
            except Garbage:
                add_one(return_one())

        outer(context)

    assert execute_pipeline(recurse).success
    assert called['throws'] is True


def test_pipeline_has_solid_def():
    @composite_solid(outputs=[OutputDefinition()])
    def inner(_context):
        return add_one(return_one())

    @composite_solid
    def outer(context):
        add_one(inner(context))

    @pipeline
    def a_pipeline(context):
        outer(context)

    assert a_pipeline.has_solid_def('add_one')
    assert a_pipeline.has_solid_def('outer')
    assert a_pipeline.has_solid_def('inner')


def test_repositry_has_solid_def():
    @composite_solid(outputs=[OutputDefinition()])
    def inner(_context):
        return add_one(return_one())

    @composite_solid
    def outer(context):
        add_one(inner(context))

    @pipeline
    def a_pipeline(context):
        outer(context)

    repo_def = RepositoryDefinition.eager_construction(
        name='has_solid_def_test', pipelines=[a_pipeline]
    )

    assert repo_def.solid_def_named('inner')
