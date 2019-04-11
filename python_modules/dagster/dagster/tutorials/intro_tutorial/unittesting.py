from dagster import (
    DependencyDefinition,
    InputDefinition,
    OutputDefinition,
    PipelineDefinition,
    SolidInstance,
    execute_solid,
    execute_solids,
    lambda_solid,
    Int,
)


@lambda_solid(
    inputs=[InputDefinition('num1', Int), InputDefinition('num2', Int)],
    output=OutputDefinition(Int),
)
def adder(num1, num2):
    return num1 + num2


@lambda_solid(
    inputs=[InputDefinition('num1', Int), InputDefinition('num2', Int)],
    output=OutputDefinition(Int),
)
def multer(num1, num2):
    return num1 * num2


def define_part_fourteen_step_one_pipeline():
    # (a + b) * (c + d)

    return PipelineDefinition(
        name='part_fourteen_step_one_pipeline',
        solids=[adder, multer],
        dependencies={
            SolidInstance(adder.name, 'a_plus_b'): {},
            SolidInstance(adder.name, 'c_plus_d'): {},
            SolidInstance(multer.name, 'final'): {
                'num1': DependencyDefinition('a_plus_b'),
                'num2': DependencyDefinition('c_plus_d'),
            },
        },
    )


def execute_test_only_final():
    solid_result = execute_solid(
        define_part_fourteen_step_one_pipeline(), 'final', inputs={'num1': 3, 'num2': 4}
    )
    assert solid_result.success
    assert solid_result.transformed_value() == 12


def execute_test_a_plus_b_final_subdag():
    results = execute_solids(
        define_part_fourteen_step_one_pipeline(),
        ['a_plus_b', 'final'],
        inputs={'a_plus_b': {'num1': 2, 'num2': 4}, 'final': {'num2': 6}},
    )

    assert results['a_plus_b'].transformed_value() == 6
    assert results['final'].transformed_value() == 36
