from dagster import (
    DependencyDefinition,
    Field,
    InputDefinition,
    OutputDefinition,
    PipelineDefinition,
    SolidInstance,
    define_stub_solid,
    execute_pipeline,
    lambda_solid,
    solid,
    types,
)


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


@lambda_solid(
    inputs=[
        InputDefinition('num1', types.Int),
        InputDefinition('num2', types.Int),
    ],
    output=OutputDefinition(types.Int),
)
def multer(num1, num2):
    return num1 * num2


def define_part_fourteen_step_one_pipeline():
    # (a + b) * (c + d)

    return PipelineDefinition(
        name='part_fourteen_step_one_pipeline',
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


def test_only_final():
    pipeline = PipelineDefinition.create_single_solid_pipeline(
        define_part_fourteen_step_one_pipeline(),
        'final',
        injected_solids={
            'final': {
                'num1': define_stub_solid('stub_a', 3),
                'num2': define_stub_solid('stub_b', 4),
            }
        }
    )

    result = execute_pipeline(pipeline)

    assert result.success
    assert len(result.result_list) == 3
    assert result.result_for_solid('stub_a').transformed_value() == 3
    assert result.result_for_solid('stub_b').transformed_value() == 4
    assert result.result_for_solid('final').transformed_value() == 12


def test_a_plus_b_final_subdag():
    pipeline = PipelineDefinition.create_sub_pipeline(
        define_part_fourteen_step_one_pipeline(),
        ['a_plus_b', 'final'],
        ['final'],
        injected_solids={
            'a_plus_b': {
                'num1': define_stub_solid('stub_a', 2),
                'num2': define_stub_solid('stub_b', 4),
            },
            'final': {
                'num2': define_stub_solid('stub_c_plus_d', 6),
            }
        },
    )

    pipeline_result = execute_pipeline(pipeline)

    assert pipeline_result.result_for_solid('a_plus_b').transformed_value() == 6
    assert pipeline_result.result_for_solid('final').transformed_value() == 36
