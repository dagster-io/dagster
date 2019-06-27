# pylint: disable=no-value-for-parameter

from dagster import (
    pipeline,
    CompositeSolidDefinition,
    lambda_solid,
    Int,
    InputDefinition,
    SolidInvocation,
    DependencyDefinition,
    OutputDefinition,
    Float,
)


@lambda_solid(inputs=[InputDefinition('num', Int)])
def add_one(num):
    return num + 1


@lambda_solid(inputs=[InputDefinition('num')])
def div_two(num):
    return num / 2


add_two = CompositeSolidDefinition(
    'add_two',
    solid_defs=[add_one],
    dependencies={
        SolidInvocation('add_one', 'adder_1'): {},
        SolidInvocation('add_one', 'adder_2'): {'num': DependencyDefinition('adder_1')},
    },
    input_mappings=[InputDefinition('num', Int).mapping_to('adder_1', 'num')],
    output_mappings=[OutputDefinition(Int).mapping_from('adder_2')],
)

add_four = CompositeSolidDefinition(
    'add_four',
    solid_defs=[add_two],
    dependencies={
        SolidInvocation('add_two', 'adder_1'): {},
        SolidInvocation('add_two', 'adder_2'): {'num': DependencyDefinition('adder_1')},
    },
    input_mappings=[InputDefinition('num', Int).mapping_to('adder_1', 'num')],
    output_mappings=[OutputDefinition(Int).mapping_from('adder_2')],
)

div_four = CompositeSolidDefinition(
    'div_four',
    solid_defs=[div_two],
    dependencies={
        SolidInvocation('div_two', 'div_1'): {},
        SolidInvocation('div_two', 'div_2'): {'num': DependencyDefinition('div_1')},
    },
    input_mappings=[InputDefinition('num', Int).mapping_to('div_1', 'num')],
    output_mappings=[OutputDefinition(Float).mapping_from('div_2')],
)


@pipeline
def composition():
    div_four(add_four())
