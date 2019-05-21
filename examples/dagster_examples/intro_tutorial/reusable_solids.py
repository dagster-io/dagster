from dagster import (
    DependencyDefinition,
    InputDefinition,
    OutputDefinition,
    PipelineDefinition,
    SolidInstance,
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


def define_reusable_solids_pipeline():
    # (a + b) * (c + d)

    return PipelineDefinition(
        name='reusable_solids_pipeline',
        solids=[adder, multer],
        dependencies={
            SolidInstance('adder', 'a_plus_b'): {},
            SolidInstance('adder', 'c_plus_d'): {},
            SolidInstance('multer', 'final'): {
                'num1': DependencyDefinition('a_plus_b'),
                'num2': DependencyDefinition('c_plus_d'),
            },
        },
    )
