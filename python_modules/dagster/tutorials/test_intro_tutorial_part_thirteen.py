from dagster import (
    DependencyDefinition,
    Field,
    InputDefinition,
    OutputDefinition,
    PipelineDefinition,
    SolidInstance,
    execute_pipeline,
    lambda_solid,
    solid,
    types,
)


@solid(config_field=Field(types.Int), outputs=[OutputDefinition(types.Int)])
def load_a(info):
    return info.config


@solid(config_field=Field(types.Int), outputs=[OutputDefinition(types.Int)])
def load_b(info):
    return info.config


@lambda_solid(
    inputs=[
        InputDefinition('a', types.Int),
        InputDefinition('b', types.Int),
    ],
    output=OutputDefinition(types.Int),
)
def a_plus_b(a, b):
    return a + b


def define_part_thirteen_step_one_pipeline():
    return PipelineDefinition(
        name='part_thirteen_step_one_pipeline',
        solids=[load_a, load_b, a_plus_b],
        dependencies={
            'a_plus_b': {
                'a': DependencyDefinition('load_a'),
                'b': DependencyDefinition('load_b'),
            }
        }
    )


def test_part_thirteen_step_one():
    pipeline_result = execute_pipeline(
        define_part_thirteen_step_one_pipeline(),
        {
            'solids': {
                'load_a': {
                    'config': 234,
                },
                'load_b': {
                    'config': 384
                },
            },
        },
    )

    assert pipeline_result.success
    solid_result = pipeline_result.result_for_solid('a_plus_b')
    assert solid_result.transformed_value() == 234 + 384


@solid(
    config_field=Field(types.Int),
    outputs=[OutputDefinition(types.Int)],
)
def load_number(info):
    return info.config


@lambda_solid(
    inputs=[
        InputDefinition('num1', types.Int),
        InputDefinition('num2', types.Int),
    ],
    output=OutputDefinition(types.Int),
)
def adder(num1, num2):
    return num1 + num2


def define_part_thirteen_step_two_pipeline():
    return PipelineDefinition(
        name='part_thirteen_step_two_pipeline',
        solids=[load_number, adder],
        dependencies={
            SolidInstance('load_number', alias='load_a'): {},
            SolidInstance('load_number', alias='load_b'): {},
            SolidInstance('adder', alias='a_plus_b'): {
                'num1': DependencyDefinition('load_a'),
                'num2': DependencyDefinition('load_b'),
            }
        }
    )


def test_part_thirteen_step_two():
    pipeline_result = execute_pipeline(
        define_part_thirteen_step_two_pipeline(),
        {
            'solids': {
                'load_a': {
                    'config': 23,
                },
                'load_b': {
                    'config': 38
                },
            },
        },
    )

    assert pipeline_result.success
    solid_result = pipeline_result.result_for_solid('a_plus_b')
    assert solid_result.transformed_value() == 23 + 38


@lambda_solid(
    inputs=[
        InputDefinition('num1', types.Int),
        InputDefinition('num2', types.Int),
    ],
    output=OutputDefinition(types.Int),
)
def multer(num1, num2):
    return num1 * num2


def define_part_thirteen_step_three_pipeline():
    # (a + b) * (c + d)

    return PipelineDefinition(
        name='part_thirteen_step_three_pipeline',
        solids=[load_number, adder, multer],
        dependencies={
            SolidInstance(load_number.name, 'a'): {},
            SolidInstance(load_number.name, 'b'): {},
            SolidInstance(load_number.name, 'c'): {},
            SolidInstance(load_number.name, 'd'): {},
            SolidInstance(adder.name, 'a_plus_b'): {
                'num1': DependencyDefinition('a'),
                'num2': DependencyDefinition('b'),
            },
            SolidInstance(adder.name, 'c_plus_d'): {
                'num1': DependencyDefinition('c'),
                'num2': DependencyDefinition('d'),
            },
            SolidInstance(multer.name, 'final'): {
                'num1': DependencyDefinition('a_plus_b'),
                'num2': DependencyDefinition('c_plus_d'),
            },
        },
    )


def test_run_whole_pipeline():
    pipeline = define_part_thirteen_step_three_pipeline()
    pipeline_result = execute_pipeline(
        pipeline, {
            'solids': {
                'a': {
                    'config': 2,
                },
                'b': {
                    'config': 6,
                },
                'c': {
                    'config': 4,
                },
                'd': {
                    'config': 8,
                },
            },
        }
    )

    assert pipeline_result.success

    assert pipeline_result.result_for_solid('a_plus_b').transformed_value() == 8
    assert pipeline_result.result_for_solid('c_plus_d').transformed_value() == 12
    assert pipeline_result.result_for_solid('final').transformed_value() == 8 * 12
