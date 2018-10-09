# pylint: disable=W0622,W0614,W0401
from dagster import (
    DependencyDefinition,
    InputDefinition,
    PipelineDefinition,
    execute_pipeline,
    lambda_solid,
)

#   B
#  / \
# A   D
#  \ /
#   C


@lambda_solid
def solid_a():
    print('a: 1')
    return 1


@lambda_solid(inputs=[InputDefinition('arg_a')])
def solid_b(arg_a):
    print('b: {b}'.format(b=arg_a * 2))
    return arg_a * 2


@lambda_solid(inputs=[InputDefinition('arg_a')])
def solid_c(arg_a):
    print('c: {c}'.format(c=arg_a * 3))
    return arg_a * 3


@lambda_solid(inputs=[InputDefinition('arg_b'), InputDefinition('arg_c')])
def solid_d(arg_b, arg_c):
    print('d: {d}'.format(d=arg_b * arg_c))


def define_pipeline():
    return PipelineDefinition(
        name='part_three_pipeline',
        solids=[solid_d, solid_c, solid_b, solid_a],
        dependencies={
            'solid_b': {
                'arg_a': DependencyDefinition('solid_a'),
            },
            'solid_c': {
                'arg_a': DependencyDefinition('solid_a'),
            },
            'solid_d': {
                'arg_b': DependencyDefinition('solid_b'),
                'arg_c': DependencyDefinition('solid_c'),
            }
        }
    )


def test_tutorial_part_three():
    execute_pipeline(define_pipeline())


if __name__ == '__main__':
    test_tutorial_part_three()
