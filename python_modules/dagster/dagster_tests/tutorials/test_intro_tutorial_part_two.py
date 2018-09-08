# pylint: disable=W0622,W0614,W0401
from dagster import *


@lambda_solid
def solid_one():
    return 'foo'


@lambda_solid(inputs=[InputDefinition('arg_one')])
def solid_two(arg_one):
    print(arg_one * 2)


def test_tutorial_part_two():
    pipeline_result = execute_pipeline(
        PipelineDefinition(
            solids=[solid_one, solid_two],
            dependencies={
                'solid_two': {
                    'arg_one': DependencyDefinition('solid_one'),
                },
            }
        )
    )

    assert pipeline_result.success
    return pipeline_result


if __name__ == '__main__':
    test_tutorial_part_two()
