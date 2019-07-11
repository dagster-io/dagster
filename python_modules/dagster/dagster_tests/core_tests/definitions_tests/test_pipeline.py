# pylint: disable=no-value-for-parameter

from dagster import (
    DependencyDefinition,
    Field,
    InputDefinition,
    Int,
    OutputDefinition,
    PipelineDefinition,
    Output,
    execute_pipeline,
    lambda_solid,
    solid,
    pipeline,
)


def builder(graph):
    return graph.add_one(graph.return_one())


@lambda_solid
def return_one():
    return 1


@lambda_solid(input_defs=[InputDefinition('num')])
def add_one(num):
    return num + 1


def test_basic_use_case():
    pipeline_def = PipelineDefinition(
        name='basic',
        solid_defs=[return_one, add_one],
        dependencies={'add_one': {'num': DependencyDefinition('return_one')}},
    )

    assert execute_pipeline(pipeline_def).result_for_solid('add_one').output_value() == 2


def test_basic_use_case_with_dsl():
    @pipeline
    def test():
        return add_one(num=return_one())

    assert execute_pipeline(test).result_for_solid('add_one').output_value() == 2


def test_two_inputs_without_dsl():
    @lambda_solid(input_defs=[InputDefinition('num_one'), InputDefinition('num_two')])
    def add(num_one, num_two):
        return num_one + num_two

    @lambda_solid
    def return_two():
        return 2

    @lambda_solid
    def return_three():
        return 3

    pipeline_def = PipelineDefinition(
        solid_defs=[add, return_two, return_three],
        dependencies={
            'add': {
                'num_one': DependencyDefinition('return_two'),
                'num_two': DependencyDefinition('return_three'),
            }
        },
    )

    assert execute_pipeline(pipeline_def).result_for_solid('add').output_value() == 5


def test_two_inputs_with_dsl():
    @lambda_solid(input_defs=[InputDefinition('num_one'), InputDefinition('num_two')])
    def add(num_one, num_two):
        return num_one + num_two

    @lambda_solid
    def return_two():
        return 2

    @lambda_solid
    def return_three():
        return 3

    @pipeline
    def test():
        return add(num_one=return_two(), num_two=return_three())

    assert execute_pipeline(test).result_for_solid('add').output_value() == 5


def test_basic_aliasing_with_dsl():
    @pipeline
    def test():
        return add_one.alias('renamed')(num=return_one())

    assert execute_pipeline(test).result_for_solid('renamed').output_value() == 2


def test_diamond_graph():
    @solid(output_defs=[OutputDefinition(name='value_one'), OutputDefinition(name='value_two')])
    def emit_values(_context):
        yield Output(1, 'value_one')
        yield Output(2, 'value_two')

    @lambda_solid(input_defs=[InputDefinition('num_one'), InputDefinition('num_two')])
    def add(num_one, num_two):
        return num_one + num_two

    @pipeline
    def diamond_pipeline():
        value_one, value_two = emit_values()
        return add(num_one=add_one(num=value_one), num_two=add_one.alias('renamed')(num=value_two))

    result = execute_pipeline(diamond_pipeline)

    assert result.result_for_solid('add').output_value() == 5


def test_two_cliques():
    @lambda_solid
    def return_two():
        return 2

    @pipeline
    def diamond_pipeline():
        return (return_one(), return_two())

    result = execute_pipeline(diamond_pipeline)

    assert result.result_for_solid('return_one').output_value() == 1
    assert result.result_for_solid('return_two').output_value() == 2


def test_deep_graph():
    @solid(config_field=Field(Int))
    def download_num(context):
        return context.solid_config

    @lambda_solid(input_defs=[InputDefinition('num')])
    def unzip_num(num):
        return num

    @lambda_solid(input_defs=[InputDefinition('num')])
    def ingest_num(num):
        return num

    @lambda_solid(input_defs=[InputDefinition('num')])
    def subsample_num(num):
        return num

    @lambda_solid(input_defs=[InputDefinition('num')])
    def canonicalize_num(num):
        return num

    @lambda_solid(input_defs=[InputDefinition('num')])
    def load_num(num):
        return num + 3

    @pipeline
    def test():
        return load_num(
            num=canonicalize_num(
                num=subsample_num(num=ingest_num(num=unzip_num(num=download_num())))
            )
        )

    result = execute_pipeline(test, {'solids': {'download_num': {'config': 123}}})
    assert result.result_for_solid('canonicalize_num').output_value() == 123
    assert result.result_for_solid('load_num').output_value() == 126
